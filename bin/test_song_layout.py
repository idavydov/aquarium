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
        for text in ('   C   Am', 'Dm Dm/c G', 'A* A* Hm', 'Em+f# Em+g A+7', 'Am С G',
                     'Cm(III) G/f#(III)', 'A D D/с#',
                     'A7sus4 Aadd13- G6add9+', 'B/5- B/5-/g', 'C/5+/d# Bm/5-/c#',
                     'F+7add11+/d F+7/5-/c', 'G+7/h G+7/a', 'Em/f#+a H7(II)Em',
                     'Dsus4:D G*F* CF G,', 'Am, Em D - 2p.',
                     'Am,Em Am!!! C! A7_____________', 'Esus2… - 7p…',
                     'A Dm ,C G', 'D D C C - 4 p.', 'G (III) F Em',
                     '(Dm Gm6/b Gm6/a Dm/f Gsus2/e*) = Dm* - 6p.',
                     'G(III):G7(III):G6(III): G7(III)*', '…G A7/c#', '_____ C(III) H B H',
                     '-8~~ -11~', '-10~ E -13~', 'H -10~ -13~',
                     '5:II 5:III', '   H----------3-1', '-----1-0------------1-0-----------0-',
                     '2-------2-----------------------2-------2-------------',
                     'D—0-------------------------', 'E-0—9-10---10-12-10h11-12',
                     'E-4h5-3-0----', 'E-5p3-0---', 'G-5/7-5---'):
            self.assertTrue(musical_line(text), text)
        for text in ('И мы несём свою вахту', 'Here comes the sun', 'Каподастр на 3-м ладу', '....', '(1998)'):
            self.assertFalse(musical_line(text), text)

    def test_whole_chord_verse_scrolls_but_next_plain_verse_wraps(self):
        output = str(song_layout('  C&nbsp; Am<br/>Первая строка<br/>Вторая строка<br/>'
                                 ' Dm G<br/>Третья строка<br/>&nbsp;<br/>Обычный куплет<br/>'))
        self.assertEqual(output.count('class="song-passage verse-block"'), 1)
        self.assertIn('song-line">Вторая строка', output)
        self.assertNotIn('song-prose song-line">Вторая строка', output)
        self.assertIn('song-prose song-line">Обычный куплет', output)
        self.assertEqual(visible_lines(output), ['C\u00a0 Am', 'Первая строка', 'Вторая строка',
                                                ' Dm G', 'Третья строка', '\u00a0', 'Обычный куплет'])

    def test_separate_chord_verses_have_separate_scroll_areas(self):
        output = str(song_layout('Am<br/>Первый куплет<br/><br/>C<br/>Второй куплет<br/>'))
        self.assertEqual(output.count('class="song-passage verse-block"'), 2)

    def test_tab_interrupts_verse_and_keeps_its_own_chord_heading(self):
        output = str(song_layout('C<br/>Куплет<br/> Am<br/>E-0---<br/>H-1---<br/>G-2---<br/>'
                                 'Dm<br/>Продолжение куплета<br/>'))
        self.assertEqual(output.count('class="song-passage verse-block"'), 2)
        parser = MusicBlocks()
        parser.feed(output)
        self.assertEqual(len(parser.blocks), 1)
        self.assertIn('Am', parser.blocks[0])
        self.assertNotIn('Куплет', parser.blocks[0])

    def test_unlabelled_tab_strings_share_groups_of_six(self):
        output = str(song_layout('Dm Am E<br/>' + '-----1-0---<br/>' * 12 + 'Текст<br/>'))
        parser = MusicBlocks()
        parser.feed(output)
        self.assertEqual(len(parser.blocks), 2)
        self.assertEqual(parser.blocks[0].count('-----1-0---'), 6)
        self.assertEqual(parser.blocks[1].count('-----1-0---'), 6)
        self.assertIn('song-prose song-line">Текст', output)

    def test_unicode_dashes_do_not_split_tab_strings_or_change_text(self):
        raw = 'G------2---<br/>D—0-------<br/>A----------<br/>E-0—0------<br/>'
        output = str(song_layout(raw))
        parser = MusicBlocks()
        parser.feed(output)
        self.assertEqual(len(parser.blocks), 1)
        self.assertIn('D—0-------', parser.blocks[0])
        self.assertIn('E-0—0------', parser.blocks[0])

    def test_chord_annotation_inside_incomplete_riff_keeps_strings_together(self):
        raw = 'D<br/>G-----9-7-<br/>Dadd9(X) E9-/d(IX) G6/d(VIII)<br/>'
        raw += 'D----7----<br/>A-7h9-----<br/>E---------<br/>'
        output = str(song_layout(raw))
        parser = MusicBlocks()
        parser.feed(output)
        self.assertEqual(len(parser.blocks), 1)
        self.assertIn('Dadd9(X)', parser.blocks[0])
        self.assertEqual(visible_lines(output), visible_lines(raw))

    def test_compound_chords_keep_whole_verse_in_one_region(self):
        raw = 'F+7add11+/d C<br/>Первая строка<br/>F+7/5-/c Em<br/>Вторая строка<br/>'
        output = str(song_layout(raw))
        self.assertEqual(output.count('class="song-passage verse-block"'), 1)
        self.assertNotIn('song-prose', output)
        self.assertEqual(visible_lines(output), visible_lines(raw))

    def test_sustained_notes_keep_sung_fragments_aligned(self):
        raw = '-8~~ -11~<br/>-10~ E -13~<br/>А-мито-<br/>Ещё один, упавший вниз.<br/>-бо<br/>'
        output = str(song_layout(raw))
        self.assertEqual(output.count('class="song-passage verse-block"'), 1)
        self.assertNotIn('song-prose', output)
        self.assertEqual(visible_lines(output), visible_lines(raw))

    def test_real_altered_chord_verses_do_not_escape_to_prose(self):
        root = Path(__file__).resolve().parent.parent / 'content/аккорды'
        for name in ['Боже,_храни_полярников', 'Волки_и_вороны', 'С_той_стороны_зеркального_стекла']:
            source = (root / (name + '.html')).read_text()
            raw = source.split('{% raw %}', 1)[1].split('{% endraw %}', 1)[0]
            output = str(song_layout(raw, name))
            self.assertGreaterEqual(output.count('class="song-passage verse-block"'), 2, name)

    def test_mountain_crystal_ending_riff_remains_one_group(self):
        source = (Path(__file__).resolve().parent.parent / 'content/аккорды/Горный_хрусталь.html').read_text()
        raw = source.split('{% raw %}', 1)[1].split('{% endraw %}', 1)[0]
        parser = MusicBlocks()
        parser.feed(str(song_layout(raw, 'Горный хрусталь')))
        last = parser.blocks[-1]
        for string in ['G-----9-7-', 'D----7----', 'A-7h9-----', 'E---------']:
            self.assertIn(string, last)
        columns = [next(line.index(string) for line in last.splitlines() if string in line)
                   for string in ['G-----9-7-', 'D----7----', 'A-7h9-----', 'E---------']]
        self.assertEqual(len(set(columns)), 1)

    def test_city_unlabelled_tabs_are_not_part_of_lyric_verse(self):
        source = (Path(__file__).resolve().parent.parent / 'content/аккорды/Город.html').read_text()
        raw = source.split('{% raw %}', 1)[1].split('{% endraw %}', 1)[0]
        output = str(song_layout(raw, 'Город'))
        parser = MusicBlocks()
        parser.feed(output)
        self.assertTrue(any('-----1-0------------1-0-----------0-' in block for block in parser.blocks))
        self.assertNotIn('Под небом голубым', ''.join(parser.blocks))

    def test_two_trains_first_verse_includes_starred_chords(self):
        source = (Path(__file__).resolve().parent.parent / 'content/аккорды/Два_поезда.html').read_text()
        raw = source.split('{% raw %}', 1)[1].split('{% endraw %}', 1)[0]
        output = str(song_layout(raw, 'Два поезда'))
        self.assertEqual(output.count('class="song-passage verse-block"'), 1)
        self.assertIn('song-prose song-line">\nЕсли ты рододендрон', output)

    def test_author_without_blank_separator_stays_outside_verse(self):
        output = str(song_layout('<span style="color:red">Песня<br/></span>'
                                 '<i>Б. Гребенщиков</i>&nbsp;<br/>C9<br/>Первый куплет<br/>', 'Песня'))
        credit, verse = output.split('class="song-passage verse-block"', 1)
        self.assertIn('song-prose song-line', credit)
        self.assertIn('<i>Б. Гребенщиков</i>', credit)
        self.assertNotIn('Б. Гребенщиков', verse)
        self.assertIn('Первый куплет', verse)

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
