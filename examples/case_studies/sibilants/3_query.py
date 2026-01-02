from polyglotdb import CorpusContext


def main():
    corpus_name = "ParlBleu-subset"
    utterances_export_path = "./output/ParlBleu-subset_utterances.csv"
    sibilants_export_path = "./output/ParlBleu-subset_sibilants.csv"

    # Getting utterances
    print("Querying all utterances...")
    with CorpusContext(corpus_name) as c:
        q = c.query_graph(c.utterance).columns(
            c.utterance.speaker.name.column_name("speaker"),
            c.utterance.id.column_name("utterance_label"),
            c.utterance.begin.column_name("utterance_begin"),
            c.utterance.end.column_name("utterance_end"),
            c.utterance.following.begin.column_name("following_utterance_begin"),
            c.utterance.following.end.column_name("following_utterance_end"),
            c.utterance.discourse.name.column_name("discourse"),
            c.utterance.discourse.speech_begin.column_name("discourse_begin"),
            c.utterance.discourse.speech_end.column_name("discourse_end"),
        )
        q.order_by(c.phone.discourse.name)
        q.to_csv(utterances_export_path)

    # Getting sibilants
    print("Querying all onset, pre-vocalic voiceless sibilant tokens >= 50 ms in duration...")
    with CorpusContext(corpus_name) as c:
        q = (
            c.query_graph(c.phone)
            .filter(
                c.phone.label.in_(["s", "ʃ"]),
                c.phone.following.subset == "vowel",
                c.phone.begin == c.phone.syllable.begin,
                c.phone.duration >= 0.05,
            )
            .columns(
                c.phone.discourse.name.column_name("discourse"),
                c.phone.utterance.speaker.name.column_name("speaker"),
                c.phone.utterance.speaker.gender.column_name("gender"),
                c.phone.label.column_name("phone"),
                c.phone.duration.column_name("phone_duration"),
                c.phone.begin.column_name("phone_begin"),
                c.phone.end.column_name("phone_end"),
                c.phone.word.phone.position.column_name("phone_position"),
                c.phone.previous.label.column_name("previous_phone"),
                c.phone.following.label.column_name("following_phone"),
                c.phone.syllable.label.column_name("syllable"),
                c.phone.syllable.begin.column_name("syllable_begin"),
                c.phone.syllable.end.column_name("syllable_end"),
                c.phone.word.label.column_name("word"),
                c.phone.word.transcription.column_name("transcription"),
                c.phone.syllable.word.begin.column_name("word_begin"),
                c.phone.syllable.word.end.column_name("word_end"),
                c.phone.syllable.word.utterance.begin.column_name("utterance_begin"),
                c.phone.syllable.word.utterance.begin.column_name("utterance_end"),
            )
        )
        q.order_by(c.phone.discourse.name)
        q.to_csv(sibilants_export_path)


if __name__ == "__main__":
    main()
