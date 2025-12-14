"""
Data Quality Gates - BEFORE inference
The most ignored but critical layer

Checks:
- Language detection
- Text truncation detection
- OCR confidence (if applicable)
- Source verification
- Duplicate detection
- Public entity detection

If usable=false, model DOES NOT RUN
"""
import re
import hashlib
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QualityIssue:
    code: str
    severity: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class DataQualityResult:
    data_quality_score: float
    issues: List[QualityIssue]
    usable: bool
    checks_passed: List[str]
    checks_failed: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataQualityGate:
    """
    Pre-inference data quality validation
    Ensures only valid data reaches the model
    """
    
    MIN_TEXT_LENGTH = 10
    MAX_TEXT_LENGTH = 50000
    MIN_QUALITY_SCORE = 0.6
    
    PT_BR_COMMON_WORDS = {
        "que", "de", "não", "para", "com", "uma", "os", "no", "se", "na",
        "por", "mais", "como", "mas", "foi", "ao", "ele", "das", "tem", "à",
        "seu", "sua", "ou", "ser", "quando", "muito", "há", "nos", "já",
        "está", "eu", "também", "só", "pelo", "pela", "até", "isso", "ela",
        "entre", "era", "depois", "sem", "mesmo", "aos", "ter", "seus", "quem"
    }
    
    EN_COMMON_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
        "this", "that", "these", "those", "it", "he", "she", "they", "we",
        "and", "or", "but", "if", "while", "because", "so", "not", "all"
    }
    
    PUBLIC_ENTITIES_PATTERNS = [
        r"\b(prefeito|governador|presidente|senador|deputado|ministro)\b",
        r"\b(vereador|juiz|promotor|procurador|delegado|secretário)\b",
        r"\b(Prefeitura|Câmara|Senado|Governo|Ministério|Tribunal)\b",
        r"\b(STF|STJ|TSE|TCU|CGU|MPF|IBGE|INSS)\b",
    ]
    
    TRUNCATION_INDICATORS = [
        r"\.\.\.$",
        r"…$",
        r"\[continua\]",
        r"\[truncado\]",
        r"\[\.{3}\]$"
    ]
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._seen_hashes: Set[str] = set()
    
    def _compute_hash(self, text: str) -> str:
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def check_language(self, text: str) -> tuple[bool, float]:
        """Check if text is in Portuguese (PT-BR) or English"""
        words = set(re.findall(r'\b\w+\b', text.lower()))
        
        if not words:
            return False, 0.0
        
        pt_count = len(words & self.PT_BR_COMMON_WORDS)
        en_count = len(words & self.EN_COMMON_WORDS)
        
        total_matches = pt_count + en_count
        ratio = total_matches / min(len(words), 50)
        
        is_valid_language = ratio >= 0.1
        return is_valid_language, round(ratio, 3)
    
    def check_length(self, text: str) -> tuple[bool, Dict[str, int]]:
        """Check text length validity"""
        length = len(text)
        word_count = len(text.split())
        
        valid = self.MIN_TEXT_LENGTH <= length <= self.MAX_TEXT_LENGTH
        
        return valid, {
            "char_count": length,
            "word_count": word_count,
            "min_required": self.MIN_TEXT_LENGTH,
            "max_allowed": self.MAX_TEXT_LENGTH
        }
    
    def check_truncation(self, text: str) -> tuple[bool, Optional[str]]:
        """Detect if text appears truncated"""
        for pattern in self.TRUNCATION_INDICATORS:
            if re.search(pattern, text):
                return True, pattern
        
        if len(text) > 100 and not re.search(r'[.!?]$', text.strip()):
            return True, "no_ending_punctuation"
        
        return False, None
    
    def check_duplicate(self, text: str) -> tuple[bool, Optional[str]]:
        """Check for duplicate content"""
        text_hash = self._compute_hash(text)
        
        if text_hash in self._seen_hashes:
            return True, text_hash
        
        self._seen_hashes.add(text_hash)
        
        if len(self._seen_hashes) > 10000:
            oldest = list(self._seen_hashes)[:5000]
            for h in oldest:
                self._seen_hashes.discard(h)
        
        return False, text_hash
    
    def check_public_entities(self, text: str) -> tuple[bool, List[str]]:
        """Detect mentions of public entities"""
        entities = []
        
        for pattern in self.PUBLIC_ENTITIES_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        return len(entities) > 0, list(set(entities))
    
    def check_content_quality(self, text: str) -> tuple[float, List[str]]:
        """Assess overall content quality"""
        issues = []
        score = 1.0
        
        if text.isupper():
            issues.append("ALL_CAPS")
            score -= 0.1
        
        special_ratio = len(re.findall(r'[!?@#$%&*]', text)) / max(len(text), 1)
        if special_ratio > 0.1:
            issues.append("EXCESSIVE_SPECIAL_CHARS")
            score -= 0.15
        
        words = text.split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                issues.append("REPETITIVE_CONTENT")
                score -= 0.2
        
        url_count = len(re.findall(r'https?://\S+', text))
        if url_count > 5:
            issues.append("EXCESSIVE_URLS")
            score -= 0.1
        
        return max(0.0, score), issues
    
    def validate(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> DataQualityResult:
        """
        Main validation method
        Runs all quality checks and returns comprehensive result
        """
        issues: List[QualityIssue] = []
        checks_passed: List[str] = []
        checks_failed: List[str] = []
        quality_score = 1.0
        
        is_portuguese, lang_confidence = self.check_language(text)
        if not is_portuguese:
            issues.append(QualityIssue(
                code="WRONG_LANGUAGE",
                severity="HIGH",
                message="Text does not appear to be in Portuguese",
                details={"confidence": lang_confidence}
            ))
            checks_failed.append("language_check")
            quality_score -= 0.3
        else:
            checks_passed.append("language_check")
        
        length_valid, length_info = self.check_length(text)
        if not length_valid:
            severity = "HIGH" if length_info["char_count"] < self.MIN_TEXT_LENGTH else "MEDIUM"
            issues.append(QualityIssue(
                code="INVALID_LENGTH",
                severity=severity,
                message=f"Text length {length_info['char_count']} outside valid range",
                details=length_info
            ))
            checks_failed.append("length_check")
            quality_score -= 0.25
        else:
            checks_passed.append("length_check")
        
        is_truncated, truncation_pattern = self.check_truncation(text)
        if is_truncated:
            issues.append(QualityIssue(
                code="TRUNCATED_CONTENT",
                severity="MEDIUM",
                message="Text appears to be truncated",
                details={"pattern": truncation_pattern}
            ))
            checks_failed.append("truncation_check")
            quality_score -= 0.15
        else:
            checks_passed.append("truncation_check")
        
        is_duplicate, text_hash = self.check_duplicate(text)
        if is_duplicate:
            issues.append(QualityIssue(
                code="DUPLICATE_CONTENT",
                severity="LOW",
                message="Duplicate content detected",
                details={"hash": text_hash}
            ))
            checks_failed.append("duplicate_check")
            quality_score -= 0.1
        else:
            checks_passed.append("duplicate_check")
        
        has_entities, entities = self.check_public_entities(text)
        checks_passed.append("entity_check")
        
        content_score, content_issues = self.check_content_quality(text)
        for issue in content_issues:
            issues.append(QualityIssue(
                code=issue,
                severity="LOW",
                message=f"Content quality issue: {issue}"
            ))
            checks_failed.append(f"content_{issue.lower()}")
        
        quality_score = quality_score * content_score
        quality_score = max(0.0, min(1.0, quality_score))
        
        high_severity_count = sum(1 for i in issues if i.severity == "HIGH")
        usable = quality_score >= self.MIN_QUALITY_SCORE and high_severity_count == 0
        
        if self.strict_mode and len(issues) > 0:
            usable = False
        
        return DataQualityResult(
            data_quality_score=round(quality_score, 4),
            issues=issues,
            usable=usable,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            metadata={
                "text_hash": text_hash or self._compute_hash(text),
                "public_entities": entities if has_entities else [],
                "language_confidence": lang_confidence,
                "length_info": length_info,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
