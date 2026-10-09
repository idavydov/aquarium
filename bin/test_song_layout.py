"""Focused regressions for the static mobile layout; no archive-wide browser sweep."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

from song_layout import apostrophes, clean_start_tag, musical_line, relative_font, song_context, song_layout, split_context


class VisibleLines(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag == 'br':
            self.parts.append('\n')
        elif tag not in ('img',):
            self.stack.append((tag, 'song-line' in dict(attrs).get('class', '').split()))

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1][0] == tag:
            _, line = self.stack.pop()
            if line:
                self.parts.append('\n')

    def handle_data(self, data):
        self.parts.append(data.replace('\n', '').replace('\r', ''))


def visible_lines(html):
    parser = VisibleLines()
    parser.feed(html)
    return ''.join(parser.parts).strip().splitlines()


class SongLayoutTests(unittest.TestCase):
    def test_chords_and_tabs_are_recognized_but_prose_is_not(self):
        for text in ('   C   Am', 'Dm Dm/c G', '5:II 5:III', '   H----------3-1',
                     'E-4h5-3-0----', 'E-5p3-0---', 'G-5/7-5---'):
            self.assertTrue(musical_line(text), text)
        for text in ('И мы несём свою вахту', 'Here comes the sun', 'Каподастр на 3-м ладу', '....'):
            self.assertFalse(musical_line(text), text)

    def test_chord_pair_scrolls_without_enclosing_plain_verses(self):
        output = str(song_layout('  C&nbsp; Am<br/>Первая строка<br/>Вторая строка<br/>'))
        self.assertIn('music-block', output)
        self.assertIn('song-prose song-line">Вторая строка', output)
        self.assertEqual(visible_lines(output), ['C\u00a0 Am', 'Первая строка', 'Вторая строка'])

    def test_inline_formatting_is_balanced_at_line_boundaries(self):
        output = str(song_layout('<i><span style="color:red">Em<br/>Текст<br/></span></i>'))
        self.assertIn('Em</span></i></div>', output)
        self.assertEqual(visible_lines(output), ['Em', 'Текст'])

    def test_russian_breadcrumb_uses_sentence_case(self):
        output = str(song_context('<span><a href="/">Главная</a> - ЕСТЕСТВЕННЫЕ АЛЬБОМЫ АКВАРИУМА И БГ - СИНИЙ АЛЬБОМ - электрический пёс<br/></span>'))
        self.assertIn('Естественные альбомы Аквариума и БГ', output)
        self.assertIn('Синий альбом', output)
        self.assertNotIn('Синий Альбом', output)
        self.assertNotIn('Электрический пёс', output)

    def test_original_small_font_scales_relatively(self):
        self.assertEqual(relative_font('<span style="font-size:8.0pt;color:red">'),
                         '<span style="font-size:0.8em;color:red">')

    def test_cleanup_drops_obsolete_zero_table_attributes_only(self):
        self.assertEqual(clean_start_tag('table', [('border', '0'), ('cellpadding', '0'),
                                                 ('cellspacing', '0'), ('width', '300')]),
                         '<table width="300">')
        self.assertEqual(clean_start_tag('span', [('style', 'color:red;font-size:8pt')]),
                         '<span style="color:red;font-size:0.8em">')

    def test_electric_dog_preserves_every_musical_line(self):
        source = (Path(__file__).resolve().parent.parent / 'content/аккорды/Электрический_пёс.html').read_text()
        raw = source.split('{% raw %}', 1)[1].split('{% endraw %}', 1)[0]
        # Remove only the breadcrumb, which is rendered separately in the header.
        raw = raw.split('</span>', 1)[1]
        output = str(song_layout(raw))
        self.assertEqual(visible_lines(raw), visible_lines(output))
        self.assertIn('song-prose song-line">\nИ мы несём свою вахту', output)

    def test_riff_strings_share_one_scroll_area(self):
        output = str(song_layout('....<br/> C Am<br/>E-4h5-3-0----<br/>H------------<br/>G------------<br/>....<br/>'))
        parser = MusicBlocks()
        parser.feed(output)
        self.assertEqual(len(parser.blocks), 1)
        self.assertIn('E-4h5', parser.blocks[0])
        self.assertIn('H------------', parser.blocks[0])
        self.assertIn('G------------', parser.blocks[0])

    def test_peach_blossom_riffs_scroll_independently(self):
        source = (Path(__file__).resolve().parent.parent / 'content/аккорды/Peach_blossom_road.html').read_text()
        raw = source.split('{% raw %}', 1)[1].split('{% endraw %}', 1)[0]
        parser = MusicBlocks()
        parser.feed(str(song_layout(raw, 'Peach blossom road')))
        self.assertEqual(len(parser.blocks), 13)
        for block in parser.blocks:
            strings = [line for line in block.splitlines() if line.lstrip().startswith(('E-', 'H-', 'G-', 'D-', 'A-'))]
            self.assertIn(len(strings), (3, 6))
        self.assertNotIn('Peach Blossom Road', str(song_layout(raw, 'Peach blossom road')))

    def test_named_duplicate_title_regressions(self):
        songs = ['Black_is_the_color_you_wear_today...', "Bridgit_O'Malley",
                 "Can't_stop_repeating_your_name", 'Chardash', 'Golden,_Golden',
                 "I'm_a_man_you_dont_meet_everyday", "I'll_be_on_my_way", 'If_you_needed_someone']
        for name in songs:
            source = (Path(__file__).resolve().parent.parent / 'content/аккорды' / (name + '.html')).read_text()
            raw = source.split('{% raw %}', 1)[1].split('{% endraw %}', 1)[0]
            _, body = split_context(raw)
            before = visible_lines(body)
            first_title = next(line.strip() for line in before if line.strip())
            after = visible_lines(str(song_layout(raw, name)))
            self.assertNotEqual(after[0].strip(), apostrophes(first_title), name)
            # Only the presentation heading and blank space may disappear.
            expected = [apostrophes(line) for line in before if line.strip()][1:]
            self.assertEqual([line for line in after if line.strip()], expected, name)

    def test_apostrophes_preserve_russian_punctuation(self):
        self.assertEqual(apostrophes('Isn`t it a pity; Can’t; O‘Malley; comin`; «пёс»'),
                         "Isn't it a pity; Can't; O'Malley; comin'; «пёс»")

    def test_nested_breadcrumb_and_version_subtitle_are_preserved(self):
        raw = ('<a name="old"></a><span><a href="/"><span>Главная</span></a>'
               ' - СИНИЙ АЛЬБОМ - Песня (</span><span>live</span><span>)<br/></span>'
               '<span style="color:red"><br/>ПЕСНЯ (live)<br/></span><i>Автор<br/></i>')
        self.assertIn('Синий альбом', str(song_context(raw)))
        self.assertEqual(visible_lines(str(song_layout(raw, 'Песня'))), ['(live)', 'Автор'])


class MusicBlocks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if 'music-block' in dict(attrs).get('class', '').split():
                self.blocks.append('')
                self.depth = 1
            elif self.depth:
                self.depth += 1

    def handle_endtag(self, tag):
        if tag == 'div' and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.blocks[-1] += data


if __name__ == '__main__':
    unittest.main()
