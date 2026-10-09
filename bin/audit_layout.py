#!/usr/bin/env python3
"""Export whitespace-preserving source/rendered text and layout warnings."""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from song_layout import CHORD_LETTERS, apostrophes, musical_line, split_context, tab_string

ROOT = Path(__file__).resolve().parent.parent


class SourceText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = ''
        self.table_depth = 0

    def flush(self):
        self.rows.append(self.row.rstrip())
        self.row = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            if not self.table_depth:
                self.flush()
                self.rows.append('[chord diagrams/table]')
            self.table_depth += 1
        elif not self.table_depth:
            if tag == 'br':
                self.flush()
            elif tag == 'img':
                self.row += '[image: %s]' % dict(attrs).get('src', '')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == 'table':
            self.table_depth -= 1
        elif not self.table_depth and tag in ('h1', 'h2', 'h3'):
            self.flush()

    def handle_data(self, data):
        if not self.table_depth:
            self.row += data.replace('\n', '').replace('\r', '')


class RenderedText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.blocks = []
        self.block = None
        self.line = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split()
        if tag not in ('br', 'img', 'hr', 'input', 'meta', 'link'):
            self.stack.append((tag, classes))
        if tag == 'div' and any(c in classes for c in ('verse-block', 'music-block', 'diagram-block')):
            kind = next(c for c in ('verse-block', 'music-block', 'diagram-block') if c in classes)
            self.block = dict(kind=kind, rows=[])
            self.blocks.append(self.block)
        if tag == 'div' and 'song-line' in classes:
            self.line = ''
            if not self.block:
                self.block = dict(kind='prose', rows=[])
                self.blocks.append(self.block)
        if tag == 'img' and self.line is not None:
            self.line += '[image: %s]' % attrs.get('src', '')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            return
        _, classes = self.stack.pop()
        if tag == 'div' and 'song-line' in classes:
            self.block['rows'].append(self.line.rstrip())
            self.line = None
            if self.block['kind'] == 'prose':
                self.block = None
        if tag == 'div' and any(c in classes for c in ('verse-block', 'music-block', 'diagram-block')):
            self.block = None

    def handle_data(self, data):
        if self.line is not None:
            self.line += data.replace('\n', '').replace('\r', '')


def warnings(blocks):
    result = []
    chordish = re.compile(r'^[A-H][#b♯♭]?(?:maj|min|dim|aug|sus|add|m)?(?:\d|[(/+*.:]|$)')
    for index, block in enumerate(blocks, 1):
        rows = [row.strip() for row in block['rows'] if row.strip()]
        lyrics = [row for row in rows if not musical_line(row)]
        block['lyric_count'] = len(lyrics)
        block['preview'] = [row[:90] for row in lyrics[:1] + lyrics[-1:]]
        if block['kind'] == 'verse-block' and (len(lyrics) > 12 or not lyrics):
            result.append(dict(kind='verse-length', block=index, count=len(lyrics), text=block['preview']))
        for row in rows:
            tokens = row.translate(CHORD_LETTERS).split()
            note_count = sum(bool(chordish.match(token)) for token in tokens)
            cue = re.match(r'^(?:Вступление|Проигрыш|Заключение|Кода|Соло|Припев|Бас|Флейта)\s*:', row, re.I)
            if not musical_line(row) and not cue and note_count and note_count >= len(tokens) / 2:
                result.append(dict(kind='unrecognized-chord-row', block=index, text=row))
            if not tab_string(row) and re.search(r'[-|–—]{3}', row) and re.search(r'\d', row):
                result.append(dict(kind='unrecognized-tab-row', block=index, text=row))
            if block['kind'] == 'verse-block' and re.search(r'Каподастр|Гребенщиков|Подбор:|Текст:', row, re.I):
                result.append(dict(kind='metadata-in-verse', block=index, text=row))
        if block['kind'] == 'music-block':
            strings = [tab_string(row) for row in rows if tab_string(row)]
            if len(strings) not in (1, 3, 4, 6):
                result.append(dict(kind='unusual-tab-group', block=index, strings=strings))
    return result


def alignment_warnings(source_rows, blocks):
    """Find source sung/tab passages split across output scroll regions."""
    source_rows = [apostrophes(row).strip() for row in source_rows]
    regions = {}
    cursor = 0
    for block_index, block in enumerate(blocks, 1):
        if block['kind'] == 'diagram-block':
            continue
        for row in block['rows']:
            row = row.strip()
            if not row:
                continue
            found = next((i for i in range(cursor, len(source_rows)) if source_rows[i] == row), None)
            if found is not None:
                regions[found] = block_index
                cursor = found + 1

    result = []
    passage = []
    # Examine source blank-line boundaries independently of rendered blocks.
    # Instrumental labels and annotations are not sung text.
    cue = re.compile(r'^(?:Вступление|Проигрыш|Заключение|Кода|Соло|Бас|Флейта|'
                     r'Колокол|Гудок|Мандолина|Гитара\s*\d*)\s*:', re.I)
    annotation = re.compile(r'Гребенщиков|Подбор:|Каподастр|быстро|раза|^\||^:|[■]', re.I)
    for index, row in enumerate(source_rows + ['']):
        if row and not row.startswith('[chord diagrams'):
            passage.append(index)
            continue
        rows = [source_rows[i] for i in passage]
        lyrics = [text for text in rows if not musical_line(text)
                  and re.search(r'[a-zа-яё]', text, re.I) and not annotation.search(text)]
        if lyrics and any(tab_string(text) for text in rows) and not any(cue.match(text) for text in rows):
            owners = sorted({regions[i] for i in passage if i in regions})
            if len(owners) > 1 or any(blocks[i - 1]['kind'] == 'prose' for i in owners):
                result.append(dict(kind='split-sung-tab-passage', blocks=owners,
                                   source_line=passage[0] + 1, text=[lyrics[0], lyrics[-1]]))
        passage.clear()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/tmp/aquarium-layout-audit'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'text').mkdir(exist_ok=True)
    records = []
    for source in sorted((ROOT / 'content/аккорды').glob('*.html')):
        raw = source.read_text().split('{% raw %}', 1)[1].split('{% endraw %}', 1)[0]
        _, raw = split_context(raw)
        before = SourceText()
        before.feed(raw)
        before.flush()
        generated = (ROOT / 'public/аккорды' / source.name).read_text()
        article = re.search(r'<article\b[^>]*>(.*?)</article>', generated, re.S)[1].strip()
        after = RenderedText()
        after.feed(article)
        flags = warnings(after.blocks) + alignment_warnings(before.rows, after.blocks)
        record = dict(song=source.stem, flags=flags, blocks=after.blocks)
        records.append(record)
        text = ['SOURCE (blank lines and spacing preserved; tables summarized)', *before.rows,
                '\nRENDERED BOUNDARIES']
        for index, block in enumerate(after.blocks, 1):
            text.append('[%d %s; candidate lyric lines=%d]' % (index, block['kind'], block['lyric_count']))
            text.extend(block['rows'])
        (args.output / 'text' / (source.stem + '.txt')).write_text('\n'.join(text))
    (args.output / 'records.json').write_text(json.dumps(records, ensure_ascii=False, indent=2))
    for group, subset in enumerate((records[:366], records[366:]), 1):
        summaries = [dict(song=row['song'], flags=row['flags'], passages=[
            dict(index=index, kind=block['kind'], rows=len(block['rows']), lyrics=block['lyric_count'], preview=block['preview'])
            for index, block in enumerate(row['blocks'], 1) if block['kind'] != 'prose' or any(block['rows'])
        ]) for row in subset]
        (args.output / ('review-%d.json' % group)).write_text(json.dumps(summaries, ensure_ascii=False))
    counts = Counter(flag['kind'] for row in records for flag in row['flags'])
    print(json.dumps(dict(songs=len(records), flagged_songs=sum(bool(row['flags']) for row in records),
                          flags=dict(counts), output=str(args.output)), ensure_ascii=False))


if __name__ == '__main__':
    main()
