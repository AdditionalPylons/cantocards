from typing import List, Dict
import aiohttp
import asyncio

from pathlib import Path
from urllib.request import urlretrieve
from bs4 import BeautifulSoup

import csv
import re

def parse_search_results(search_results) -> Dict:
    complete = []
    incomplete = []
    missing = []
    for term, raw_html in search_results:
        soup = BeautifulSoup(raw_html, "html.parser")

        no_matches = re.compile(r"Number of matches: 0")
        eng_def_regex = re.compile(r">english:</span>\xa0(?=<[A-Za-z]+>)?(?P<english>[A-Za-z0-9\s,;'\"\(\)\[\]\/\.\=]+)(?=</?[A-Za-z]+/?>)?[^a-zA-Z\d\s:]")
        pronunciation_regex = re.compile(r"(?P<pronunciation>\[.+?\])")
        if no_matches.search(str(soup.body)):
            missing.append(term)
            continue

        parsed = {
            "mandarin": term,
            "character": soup.body.b.string if soup.body.b else "MISSING_DATA",
            "english": eng_def_regex.search(str(soup.body)).group("english").strip() if eng_def_regex.search(str(soup.body)) else "MISSING_DATA",
            "pronunciation": pronunciation_regex.search(str(soup.body)).group("pronunciation").strip() if soup.body.a else "MISSING_DATA",
            "audio": soup.body.a["href"] if soup.body.a else "MISSING_DATA",
        }
        if "MISSING_DATA" in parsed.values():
            incomplete.append(parsed)
        else:
            complete.append(parsed)

    final = {
        "complete": complete,
        "incomplete": incomplete,
        "missing": missing,
    }
    len_final = len(final["complete"]) + len(final["incomplete"]) + len(final["missing"])
    print(f'COMPLETE: {final["complete"]}, {(len(final["complete"])/len_final)*100}%\n')
    print(f'INCOMPLETE: {final["incomplete"]}, {(len(final["incomplete"])/len_final)*100}%\n')
    print(f'MISSING: {final["missing"]}, {(len(final["missing"])/len_final)*100}%\n')
    return final

async def search(terms: List) -> Dict:

    #terms = ["下雨", "你好"]
    #connector = aiohttp.TCPConnector(limit=20, force_close=True)
    async with aiohttp.ClientSession() as session:
        results = []
        url = "https://www.taishandict.com/MySQLSearch.php"

        for term in terms:
            payload = {
                "data": term,
                "Select1": "Mandarin",
                "submit": "Search",
                "Select2": "Full",
            }
            form_data = aiohttp.FormData()
            for k, v in payload.items():
                form_data.add_field(k, v)
            async with session.post(url, data=form_data) as response:
                print(f"Searching for {term}...")
                html = await response.text()
                results.append((term, html))
        parsed = parse_search_results(results)
    return parsed

def import_vocab_list(file):

    with open(Path.cwd().joinpath(file), "r") as source:
        results = [line.strip() for line in source]
        return results


def scrape_hsk(hsk_level):

    levels = {
        1: "HSK1.txt",
        2: "HSK2.txt",
        3: "HSK3.txt",
        4: "HSK4.txt",
        5: "HSK5.txt",
        6: "HSK6.txt",
        }

    if hsk_level == 0 or hsk_level == "all":
        full_hsk_list = []
        for level in levels.values():
            full_hsk_list += [*import_vocab_list(level)]
        entries = asyncio.run(search(full_hsk_list))
    else:
        entries = asyncio.run(search(import_vocab_list(levels[hsk_level])))

    return entries


def export_audio(result_list, folder_name="collection.media"):
    print("Exporting audio files...")
    audio_dir = Path.cwd().joinpath(folder_name)
    if not audio_dir.exists():
        audio_dir.mkdir()

    for row in result_list:
        term = row.get("mandarin")
        url_extension = row.get("audio")
        if not term or not url_extension:
            continue
        url = "https://www.stephen-li.com/TaishaneseVocabulary/" + url_extension
        filepath = audio_dir.joinpath(f"{term}.mp3")
        if not filepath.exists():
            urlretrieve(url, filepath)
    print("Done exporting audio files!")


def export_entries(result_list, filename="scraped_results", extension="csv"):
    print("Writing entries to CSV file...")
    with open(Path.cwd().joinpath(f"{filename}.{extension}"), "wt") as csv_file:
        fieldnames = ["mandarin", "character", "english", "pronunciation", "audio"]

        writer = csv.DictWriter(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL, fieldnames=fieldnames)

        writer.writeheader()
        for row in result_list:
            if row.get("audio") and row.get("character"):
                row["audio"] = f"[sound:{row['character']}.mp3]"
            writer.writerow(row)
    print("Done writing CSV file!")


def main():
    complete_entries = scrape_hsk(1)["complete"]
    export_audio(complete_entries)
    export_entries(complete_entries)


if __name__ == '__main__':
    main()
