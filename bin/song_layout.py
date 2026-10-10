"""Build responsive song markup while preserving musical spacing."""
from html import escape, unescape
from html.parser import HTMLParser
import re

from markupsafe import Markup


# The source mixes modern extension notation, altered degrees (/5-), bass
# notes (+g or /g), and changes written without spaces (Dsus4:D, H7(II)Em).
CHORD_UNIT = r'[A-H][#b♯♭]?(?:(?:maj|min|dim|aug|sus|add|m|M)|\d|\+[a-h][#b♯♭]?|[+-]|/(?:\d+[+-]?|[A-Ha-h][#b♯♭]?)|\([^)]*\))*[*_!.…]*'
CHORD = re.compile(r'(?:%s)(?:[:=,]?(?:%s))*[,;]?' % (CHORD_UNIT, CHORD_UNIT))
CHORD_LETTERS = str.maketrans('АВСЕНавсен', 'ABCEHabceh')
TAB_DASHES = str.maketrans('–—−‑', '----')
INSTRUMENTAL_CUE = re.compile(
    r'^(?:Вступление|Проигрыш|Заключение|Кода|Соло|Бас|Флейта|Колокол|Гудок|'
    r'Мандолина|Гитара\s*\d*)\s*:', re.I)


def apostrophes(text):
    """Normalize Latin apostrophes without changing Russian quotes or URLs."""
    return re.sub(r"(?<=[A-Za-z])[`´‘’ʼ]|[`´‘’ʼ](?=[A-Za-z])", "'", text)


def tab_string(text):
    text = text.translate(TAB_DASHES)
    match = re.search(r'(?:^|\s)([EHGDABe])[-|][-|0-9hHpPbBrRsStTxX/\\~^().]{2,}', text)
    if match:
        return match[1]
    # Some archived six-string groups omit E/H/G/D/A/E after the first
    # group. Treat their strict dash/number notation as tabs too.
    if (re.fullmatch(r'[-|0-9][-|0-9hHpPbBrRsStTxX/\\~^().]{5,}', text.strip())
            and text.count('-') >= 2
            and (text.lstrip().startswith(('-', '|')) or text.count('-') >= 5)):
        return '?'
    return None


def musical_line(text):
    text = text.strip()
    # Hammer-ons, pull-offs and slides are part of a string line too. Testing
    # just its first few characters incorrectly split E-4h5 from H/G below it.
    if tab_string(text):
        return True
    text = re.sub(r'\b(\d+)\s+([pрr])([.…]*)', r'\1\2\3', text)
    tokens = text.split()
    # Latin-looking Cyrillic letters occur in chord rows in the old archive.
    # Normalize for recognition only; keep the rendered source text intact.
    def note(token):
        chord = token.translate(CHORD_LETTERS).lstrip('_…,').rstrip(':')
        # Parentheses also bracket entire progressions, separately from a
        # chord's balanced fret-position suffix such as Am(V).
        if chord.startswith('(') and chord.count('(') > chord.count(')'):
            chord = chord[1:]
        if chord.endswith(')') and chord.count(')') > chord.count('('):
            chord = chord[:-1]
        if CHORD.fullmatch(chord) or re.fullmatch(
                r'(?:(?:\d+:[IVX\d]+|fl\d+)[.…]*|\d+[pрr][. …]*|\([IVX]+\))', token):
            return True
        # Short, unlabelled sustained notes can sit above sung fragments.
        # They need alignment with the whole passage, not six-string slicing.
        return (re.fullmatch(r'[-|0-9][-|0-9hHpPbBrRsStTxX/\\~^().]{2,}', token)
                and re.search(r'[-|~]', token) and re.search(r'\d', token)
                and (token.startswith(('-', '|')) or re.search(r'[~^]', token)))
    return any(note(token) for token in tokens) and all(note(token) or re.fullmatch(
        r'[|:.,/–—_=…-]+', token) for token in tokens)


def relative_font(tag):
    # Original content uses a 10pt base. Keep its relative sizes while allowing
    # the reader's text-size control to scale diagrams and lyrics together.
    return re.sub(r'(font-size\s*:)\s*([\d.]+)pt',
                  lambda match: '%s%gem' % (match[1], float(match[2]) / 10),
                  tag, flags=re.I)


def theme_colors(style):
    """Keep faded ink theme-relative; discard inherited background patches."""
    greys = {'black': 0, 'gray': 128, 'grey': 128, 'darkgray': 169,
             'darkgrey': 169, 'silver': 192, 'lightgray': 211,
             'lightgrey': 211, 'white': 255}

    def adapt(match):
        color = match[2].strip().lower()
        background = bool(re.search(r'background(?:-color)?\s*:', match[1], re.I))
        if background:
            return ';' if match[1].startswith(';') else ''
        if color == 'windowtext':
            return match[1] + 'var(--text)'
        if color == 'blue':
            return match[1] + 'var(--link)'
        grey = greys.get(color)
        if re.fullmatch(r'#[0-9a-f]{6}', color):
            rgb = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
            if len(set(rgb)) == 1:
                grey = rgb[0]
            elif color in ('#d1f6ff', '#e7faff'):
                # Pale blue ink belonged to the old blue fade-in background.
                # Keep its brightness as neutral faded ink on the page surface.
                grey = sum(channel * weight for channel, weight in zip(rgb, (.2126, .7152, .0722)))
            else:
                return match[1] + 'var(--archive-' + color[1:] + ', ' + match[2] + ')'
        if grey is not None:
            return match[1] + 'color-mix(in srgb, var(--archive-ink) %g%%, var(--surface))' % (
                round((255 - grey) * 100 / 255, 3))
        return match[0]

    return re.sub(r'((?:^|;)\s*(?:color|background(?:-color)?)\s*:\s*)([^;]+)',
                  adapt, style, flags=re.I).strip('; ')


def clean_start_tag(tag, attrs, self_closing=False):
    """Normalize archived markup; keep content and presentation-bearing styles."""
    kept = []
    for name, value in attrs:
        if tag == 'table' and name in ('border', 'cellpadding', 'cellspacing') and value == '0':
            continue
        if value is None:
            kept.append(name)
        else:
            if name == 'style':
                value = theme_colors(value)
            kept.append('%s="%s"' % (name, escape(value, quote=True)))
    markup = '<' + tag + (' ' + ' '.join(kept) if kept else '')
    return relative_font(markup + ('/>' if self_closing else '>'))


class SongLines(HTMLParser):
    """Split at explicit line breaks, balancing inline markup at each boundary."""
    def __init__(self, title=None):
        super().__init__(convert_charrefs=False)
        self.title = title
        self.lines = []
        self.tokens = []
        self.text = []
        self.open_tags = []

    def flush(self):
        markup = ''.join(self.tokens) + ''.join('</%s>' % tag for tag, _ in reversed(self.open_tags))
        self.lines.append((markup, unescape(''.join(self.text))))
        self.tokens = [markup for _, markup in self.open_tags]
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'br':
            self.flush()
            return
        markup = clean_start_tag(tag, attrs)
        self.tokens.append(markup)
        if tag not in ('img', 'hr', 'input', 'meta', 'link'):
            self.open_tags.append((tag, markup))
        if tag == 'img':
            self.text.append('[image]')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.flush()
        else:
            self.tokens.append(clean_start_tag(tag, attrs, self_closing=True))
            if tag == 'img':
                self.text.append('[image]')

    def handle_endtag(self, tag):
        if any(name == tag for name, _ in self.open_tags):
            while self.open_tags:
                name, _ = self.open_tags.pop()
                self.tokens.append('</%s>' % name)
                if name == tag:
                    break
        if tag in ('h1', 'h2', 'h3'):
            self.flush()

    def handle_data(self, data):
        data = apostrophes(data)
        self.tokens.append(data)
        self.text.append(data)

    def handle_entityref(self, name):
        self.tokens.append('&%s;' % name)
        self.text.append('&%s;' % name)

    def handle_charref(self, name):
        self.tokens.append('&#%s;' % name)
        self.text.append('&#%s;' % name)

    def handle_comment(self, data):
        self.tokens.append('<!--%s-->' % data)

    def finish(self):
        if ''.join(self.text).strip():
            self.flush()
        result = []
        music = []
        strings = []
        verse = []
        leading_metadata = bool(self.title)

        # Every archived page starts with a presentation-only red title. Its
        # spelling need not match the metadata (some old copies contain typos).
        # Remove that header, never matching title phrases later in the lyrics.
        if self.title:
            first = next((i for i, (_, text) in enumerate(self.lines) if text.strip()), None)
            if first is not None and re.search(r'color\s*:\s*(?:red|#ff0000)', self.lines[first][0], re.I):
                markup, text = self.lines[first]
                suffix = re.search(r'\([^()]+\)\s*$', text.strip())
                keep_suffix = suffix and suffix[0].casefold() not in self.title.casefold()
                self.lines = self.lines[first + 1:]
                if keep_suffix:
                    self.lines.insert(0, (escape(suffix[0]), suffix[0]))
            while self.lines and not self.lines[0][1].strip():
                self.lines.pop(0)

        # Tabs in a sung passage are part of its score, including chords placed
        # beside the strings. Splitting at those tabs detaches the last chord
        # row from its lyric. Explicit instrumental sections keep their own
        # riff groups; blank lines still separate verses.
        sung_tabs = set()
        passage = []
        for index, (markup, text) in enumerate(self.lines + [('', '')]):
            if text.strip():
                passage.append(index)
                continue
            rows = [self.lines[i] for i in passage]
            has_tabs = any(tab_string(row) for _, row in rows)
            has_lyrics = any(not musical_line(row) and re.search(r'[a-zа-яё]', row, re.I)
                             and not re.search(r'<i(?:\s|>)', html, re.I)
                             and not re.search(r'Гребенщиков|Подбор:|Каподастр|^\s*[|:]|■', row, re.I)
                             for html, row in rows)
            if has_tabs and has_lyrics and not any(INSTRUMENTAL_CUE.match(row.strip()) for _, row in rows):
                sung_tabs.update(passage)
            passage.clear()

        def emit_music():
            if music:
                result.append('<div class="song-passage music-block" tabindex="0" '
                              'role="region" aria-label="Аккорды и табулатура">'
                              + ''.join(music) + '</div>')
                music.clear()
                strings.clear()

        def emit_verse():
            if not verse:
                return
            # Explicit blank lines delimit passages; do not infer verse breaks
            # from punctuation or meaning. Only chord-bearing passages need
            # shared horizontal scrolling. Ordinary prose remains wrappable.
            chords = any(musical_line(text) for _, text in verse)
            lines = ''.join('<div class="%ssong-line">%s</div>'
                            % ('' if chords else 'song-prose ', markup)
                            for markup, _ in verse)
            if chords:
                result.append('<div class="song-passage verse-block" tabindex="0" '
                              'role="region" aria-label="Аккорды и текст куплета">'
                              + lines + '</div>')
            else:
                result.append(lines)
            verse.clear()

        for index, (markup, text) in enumerate(self.lines):
            line = '<div class="song-line">%s</div>' % markup
            string = tab_string(text)
            if text.strip():
                # Author/capo credits sometimes have no empty line before the
                # first chord. Keep leading italic metadata out of that verse.
                if leading_metadata and not musical_line(text) and re.search(r'<i(?:\s|>)', markup, re.I):
                    result.append('<div class="song-prose song-line">%s</div>' % markup)
                    continue
                leading_metadata = False
            if not text.strip():
                emit_music()
                emit_verse()
                result.append('<div class="song-prose song-line">%s</div>' % markup)
            elif index in sung_tabs:
                emit_music()
                verse.append((markup, text))
            elif string:
                if strings and (len(strings) >= 6
                                or string != '?' and string in strings and not (string in ('E', 'e') and strings[-1] == 'A')):
                    emit_music()
                # Chords immediately above a tab belong to that tab group,
                # rather than pulling the introduction or verse into it.
                prefix = []
                while verse and musical_line(verse[-1][1]):
                    prefix.insert(0, verse.pop()[0])
                emit_verse()
                music.extend('<div class="song-line">%s</div>' % chord for chord in prefix)
                music.append(line)
                strings.append(string)
            else:
                # Chord annotations may sit between strings of an unfinished
                # riff. Keep them together only when the next string continues
                # this group; repeated labels still begin independent riffs.
                if strings and len(strings) < 6 and musical_line(text):
                    next_string = None
                    for _, following in self.lines[index + 1:]:
                        next_string = tab_string(following)
                        if next_string or not musical_line(following):
                            break
                    # A chord heading before a repeated E starts a new riff,
                    # including scores which omit the low sixth string. An E
                    # immediately after A (without a heading) can still be the
                    # sixth string of the current group.
                    if next_string and (next_string == '?' or next_string not in strings):
                        music.append(line)
                        continue
                emit_music()
                verse.append((markup, text))
        emit_music()
        emit_verse()
        return ''.join(result)


class SongLayout(HTMLParser):
    def __init__(self, title=None):
        super().__init__(convert_charrefs=False)
        self.title = title
        self.parts = []
        self.tokens = []
        self.table_depth = 0

    def flush(self, table=False):
        content = ''.join(self.tokens)
        self.tokens = []
        if not content.strip():
            return
        if not table:
            lines = SongLines(self.title)
            self.title = None
            lines.feed(content)
            lines.close()
            self.parts.append(lines.finish())
            return
        # Rearrange independent diagrams only; retain other table structures.
        diagram = (len(re.findall(r'<table\b', content, re.I)) == 1
                   and not re.search(r'\b(?:colspan|rowspan)\s*=', content, re.I)
                   and re.search(r'[EHGDA][-|■]{3}', content))
        if diagram:
            content = re.sub(r'<table\b', '<table class="chord-diagrams"',
                             content, count=1, flags=re.I)
        self.parts.append('<div class="song-passage diagram-block" tabindex="0" role="region" '
                          'aria-label="Схемы аккордов">%s</div>' % content)

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            if not self.table_depth:
                self.flush()
            self.table_depth += 1
        self.tokens.append(clean_start_tag(tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.tokens.append(clean_start_tag(tag, attrs, self_closing=True))

    def handle_endtag(self, tag):
        self.tokens.append('</%s>' % tag)
        if tag == 'table':
            self.table_depth -= 1
            if not self.table_depth:
                self.flush(table=True)

    def handle_data(self, data):
        self.tokens.append(apostrophes(data))

    def handle_entityref(self, name):
        self.tokens.append('&%s;' % name)

    def handle_charref(self, name):
        self.tokens.append('&#%s;' % name)

    def handle_comment(self, data):
        self.tokens.append('<!--%s-->' % data)


def split_context(content):
    # Breadcrumbs sometimes contain nested spans or an early </span>. Their
    # first explicit line break is the reliable boundary in all source pages.
    match = re.match(r'\s*(.*?<br\s*/?>)(?:\s*</(?:span|a)>)*', content, re.S | re.I)
    context = ''
    if match and re.search(r'<a\b[^>]*href=[\'"]/[\'"]', match[1]):
        context = match[1]
        content = content[match.end():]
    return context, content


class ContextText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def sentence_case(text):
    # Each breadcrumb item is one phrase, never title-case each word. Preserve
    # Russian proper names and abbreviations found in the archive's headings.
    text = text.strip()
    if text.isupper():
        text = text.lower()
    text = re.sub(r'\bбг\b', 'БГ', text, flags=re.I)
    text = re.sub(r'\bаквариум(?:а)?\b', lambda match: match[0].capitalize(), text, flags=re.I)
    return text[:1].upper() + text[1:]


def song_context(content):
    context, _ = split_context(content)
    parser = ContextText()
    parser.feed(context)
    parts = re.split(r'\s+-\s+', ''.join(parser.parts).strip())
    # The last breadcrumb repeats the song heading directly below it.
    trail = ' · '.join(escape(sentence_case(apostrophes(part))) for part in parts[1:-1] if part.strip())
    return Markup('<a class="all-songs" href="/">← Все песни</a>'
                  + (' · ' + trail if trail else ''))


def song_layout(content, title=None):
    _, content = split_context(content)
    # White underscore runs are invisible padding from the original editor.
    # Retain the source characters, but do not let them indent the intro.
    content = re.sub(r'<span\s+style="color:white(?:;[^"]*)?">(_+)</span>',
                     r'<span style="color:white;font-size:0">\1</span>', content, flags=re.I)
    parser = SongLayout(title)
    parser.feed(content)
    parser.close()
    parser.flush()
    return Markup(''.join(parser.parts))
