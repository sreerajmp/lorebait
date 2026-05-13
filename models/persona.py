from enum import Enum


class Persona(str, Enum):
    TUTOR = "tutor"
    RESEARCHER = "researcher"
    LEARNER = "learner"
