from polyglotdb import CorpusContext
from polyglotdb.acoustics.formants.refined import analyze_formant_points_refinement


def main():
    corpus_name = "ParlBleu-subset"

    with CorpusContext(corpus_name) as c:
        # Set this for your computer
        c.config.praat_path = "/Applications/Praat.app/Contents/MacOS/Praat"

        print("Refined formant calculations...")
        c.analyze_formant_tracks(vowel_label="vowel")


if __name__ == "__main__":
    main()
