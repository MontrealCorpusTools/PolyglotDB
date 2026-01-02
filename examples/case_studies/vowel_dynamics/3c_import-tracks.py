from polyglotdb import CorpusContext


def main():
    corpus_name = "ParlBleu-subset"
    fasttrack_csv_path = "./output/vowel_sample_fasttrack.csv"

    print("Loading tracks")
    with CorpusContext(corpus_name) as c:
        c.save_track_from_csv(
            "formants",
            fasttrack_csv_path,
            ["F1", "F2", "F3", "B1", "B2", "B3", "f0", "intensity", "harmonicity"],
        )


if __name__ == "__main__":
    main()
