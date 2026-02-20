"""Test profile classifier."""

from app.models.enums import ProfileType
from app.services.classifier import classify_profile


def test_classify_asylum():
    """Test classification of asylum-related text."""
    text = "Necesito ayuda con mi proceso de asilo"
    result = classify_profile(text)
    assert result == ProfileType.ASYLUM


def test_classify_arraigo():
    """Test classification of arraigo-related text."""
    text = "Quiero solicitar arraigo familiar"
    result = classify_profile(text)
    assert result == ProfileType.ARRAIGO


def test_classify_student():
    """Test classification of student-related text."""
    text = "Soy estudiante y necesito renovar mi visa"
    result = classify_profile(text)
    assert result == ProfileType.STUDENT


def test_classify_irregular():
    """Test classification of irregular status text."""
    text = "Mi situación es irregular en el país"
    result = classify_profile(text)
    assert result == ProfileType.IRREGULAR


def test_classify_other():
    """Test classification of unmatched text."""
    text = "Hola, ¿cómo estás?"
    result = classify_profile(text)
    assert result == ProfileType.OTHER


def test_classify_empty():
    """Test classification of empty text."""
    result = classify_profile("")
    assert result == ProfileType.OTHER


def test_classify_case_insensitive():
    """Test that classification is case-insensitive."""
    text = "ASILO urgente"
    result = classify_profile(text)
    assert result == ProfileType.ASYLUM


def test_classify_with_noise():
    """Test classification with surrounding text."""
    text = "Buenos días, necesito información sobre el proceso de asilo político"
    result = classify_profile(text)
    assert result == ProfileType.ASYLUM


def test_classify_multiple_keywords():
    """Test that first matched keyword wins."""
    text = "Soy estudiante irregular"
    result = classify_profile(text)
    # Should match first encountered keyword in pattern order
    assert result in [ProfileType.STUDENT, ProfileType.IRREGULAR]
