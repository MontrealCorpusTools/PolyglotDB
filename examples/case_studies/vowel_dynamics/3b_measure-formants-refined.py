from polyglotdb import CorpusContext
from polyglotdb.acoustics.formants.refined import analyze_formant_points_refinement


def main():
    corpus_name = "ParlBleu-subset"
    vowel_prototypes_path = "./ParlBleu-subset/enrichment_data/prototypes.csv"  # Change this if using different prototypes

    with CorpusContext(corpus_name) as c:
        # Set this for your computer
        c.config.praat_path = "/Applications/Praat.app/Contents/MacOS/Praat"

        print("Refined formant calculations...")
        analyze_formant_points_refinement(
            c,
            vowel_label="vowel",
            duration_threshold=0.05,
            num_iterations=20,
            vowel_prototypes_path=vowel_prototypes_path,
            output_tracks=True,
        )


if __name__ == "__main__":
    main()
