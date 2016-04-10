
from .featured import FeaturedContext


class SyllabicContext(FeaturedContext):
    def find_onsets(self):
        pass

    def find_codas(self):
        pass

    def encode_syllabic_segments(self, phones):
        pass

    def encode_number_of_syllables(self):
        pass

    def encode_syllables(self):
        pass
