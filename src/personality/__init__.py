"""
Personality Engineering Module
Provides human-like communication features for Karen
"""

from .core_personality import CorePersonality
from .empathy_engine import EmpathyEngine
from .phone_etiquette import PhoneEtiquette
from .small_talk import SmallTalkEngine
from .cultural_awareness import CulturalAwareness

__all__ = [
    'CorePersonality',
    'EmpathyEngine', 
    'PhoneEtiquette',
    'SmallTalkEngine',
    'CulturalAwareness'
]