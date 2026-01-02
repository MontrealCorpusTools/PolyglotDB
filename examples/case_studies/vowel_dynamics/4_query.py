from polyglotdb import CorpusContext


def main():
    corpus_name = "ParlBleu-subset"
    export_path = "./output/formants-refined.csv"

    print("Querying all word-final-syllable vowel tokens >= 50 ms in duration...")
    with CorpusContext(corpus_name) as c:
        q = c.query_graph(c.phone).filter(
            c.phone.syllable.end == c.phone.word.end,
            c.phone.subset == "vowel",
            c.phone.duration >= 0.05,
        )

        formants = c.phone.formants

        # Use this code if uninterpolated formant tracks are desired (make sure to comment out the next set of lines lines)
        # formants.relative_time = False
        # formants_track = formants.track

        # Use this code for interpolated formant tracks
        formants.relative_time = True
        formants_track = formants.interpolated_track
        formants_track.num_points = 9  # Change this as desired

        q = q.columns(
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
            formants_track,
        )
        q.order_by(c.phone.discourse.name)
        q.to_csv(export_path)


if __name__ == "__main__":
    main()
