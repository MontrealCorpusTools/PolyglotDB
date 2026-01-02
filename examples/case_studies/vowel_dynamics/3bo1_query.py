from polyglotdb import CorpusContext


def main():
    corpus_name = "ParlBleu-subset"
    export_path = "./output/vowels.csv"

    # Step 2: Getting the discourse name, begin and end time
    print("Querying all word-final-syllable vowel tokens >= 50 ms in duration...")
    with CorpusContext(corpus_name) as c:
        q = (
            c.query_graph(c.phone)
            .filter(
                c.phone.subset == "vowel",
                c.phone.duration >= 0.05,
            )
            .columns(
                c.phone.utterance.speaker.name.column_name("speaker"),
                c.phone.discourse.name.column_name("discourse"),
                c.phone.utterance.speaker.gender.column_name("gender"),
                c.phone.utterance.speaker.yob.column_name("yob"),
                c.phone.id.column_name("phone_id"),
                c.phone.label.column_name("phone"),
                c.phone.syllable.label.column_name("syllable"),
                c.phone.word.label.column_name("word"),
                c.phone.word.transcription.column_name("transcription"),
                c.phone.begin.column_name("phone_begin"),
                c.phone.end.column_name("phone_end"),
            )
        )
        q.order_by(c.phone.discourse.name)
        q.to_csv(export_path)


if __name__ == "__main__":
    main()
