"""Regression checks for cross-region song alignment diagnostics."""
import unittest

from audit_layout import alignment_warnings


class AlignmentAuditTests(unittest.TestCase):
    def setUp(self):
        self.rows = ['C Am', 'Первый куплет', '        E-3-4h5-0---',
                     'Dm G    H----------', '        G----------', 'Последняя строка', '']

    def test_reports_detached_chords_and_wrappable_last_lyric(self):
        blocks = [dict(kind='verse-block', rows=self.rows[:2]),
                  dict(kind='music-block', rows=self.rows[2:5]),
                  dict(kind='prose', rows=self.rows[5:6])]
        flags = alignment_warnings(self.rows, blocks)
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]['kind'], 'split-sung-tab-passage')
        self.assertEqual(flags[0]['blocks'], [1, 2, 3])

    def test_accepts_shared_passage(self):
        self.assertEqual(alignment_warnings(self.rows, [dict(kind='verse-block', rows=self.rows)]), [])

    def test_does_not_report_explicit_instrumental_section(self):
        rows = ['Вступление:', *self.rows]
        blocks = [dict(kind='prose', rows=rows[:1]), dict(kind='music-block', rows=rows[1:])]
        self.assertEqual(alignment_warnings(rows, blocks), [])

    def test_repeated_lyric_rows_map_to_the_correct_occurrence(self):
        rows = self.rows[:-1] + ['', *self.rows]
        blocks = [dict(kind='verse-block', rows=self.rows[:-1]),
                  dict(kind='music-block', rows=self.rows[:5]),
                  dict(kind='prose', rows=self.rows[5:6])]
        flags = alignment_warnings(rows, blocks)
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]['blocks'], [2, 3])


if __name__ == '__main__':
    unittest.main()
