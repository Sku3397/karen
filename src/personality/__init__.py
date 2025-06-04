"""
Personality Engineering Module
Provides human-like communication features for Karen
"""

from .core_personality import CorePersonality, PersonalityTraits, PersonalityConsistencyChecker
from .empathy_engine import EmpathyEngine
from .phone_etiquette import PhoneEtiquette
from .small_talk import SmallTalkEngine
from .cultural_awareness import CulturalAwareness
from .response_enhancer import ResponseEnhancer

__all__ = [
    'CorePersonality',
    'PersonalityTraits',
    'PersonalityConsistencyChecker',
    'EmpathyEngine', 
    'PhoneEtiquette',
    'SmallTalkEngine',
    'CulturalAwareness',
    'ResponseEnhancer'
]