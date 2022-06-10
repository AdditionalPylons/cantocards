import aiohttp
import asyncio

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from pathlib import Path
from urllib.request import urlretrieve
from typing import List
from bs4 import BeautifulSoup

import csv
import re

def parse_search_results(search_results):
    complete = []
    incomplete = []
    missing = []
    for term, raw_html in search_results:
        soup = BeautifulSoup(raw_html, "html.parser")

        no_matches = re.compile(r"Number of matches: 0")
        eng_def_regex = re.compile(r">english:</span>\xa0(<em>)?(?P<english>[A-Za-z\d\s,'-=/()&;\[\]]+)</em>?[^a-zA-Z\d\s:]")
        if no_matches.search(str(soup.body)):
            missing.append(term)
            continue

        parsed = {
            "mandarin": term,
            "character": soup.body.b.string if soup.body.b else "MISSING_DATA",
            "english": eng_def_regex.search(str(soup.body)).group("english").strip() if eng_def_regex.search(str(soup.body)) else "MISSING_DATA",
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

async def search(terms):

    async with aiohttp.ClientSession() as session:
        results = []
        no_eng = 0
        for term in terms:
            url = "https://www.stephen-li.com/TaishaneseVocabulary/MySQLSearch.php"
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
        print(full_hsk_list)
        asyncio.run(search(full_hsk_list))
    else:
        asyncio.run(search(import_vocab_list(levels[hsk_level])))

"""
OLD CODE BELOW
# TODO: REFACTOR THIS FOR THE NEW FLOW

def export_entries(self, filename="scraped_results", extension="txt"):

    with open(Path.cwd().joinpath(f"{filename}.{extension}"),
            "a+") as file:

        def write_entry(word, definition):
            if extension == "txt":
                file.write(f"{word} : {definition}\n")
            elif extension == "csv":
                writer = csv.writer(file, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
                writer.writerow([f"{word}", f"{definition}"])

        for key, value in self.scraped_results.items():
            write_entry(key, value[0])

def export_audio(self, folder_name="audio"):
    audio_dir = Path.cwd().joinpath(folder_name)
    if not audio_dir.exists():
        audio_dir.mkdir()

    for word, results in self.scraped_results.items():
            url = results[1]
            filepath = audio_dir.joinpath(f"{word}.mp3")
            if not filepath.exists():
                urlretrieve(url, filepath)

def print_results(self):
    for key, value in self.scraped_results.items():
        print(f"TERM: {key} DEF: {value[0]} CLIP: {value[1]}")

"""

asyncio.run(search(["主义"]))
#scrape_hsk(0)



class TaishaneseScraper():
    
    def __init__(self):
        self.scraped_results = {}
        self.failed_count = 0
        self.failed_entries = []

    def search_and_scrape(self, words: List, language="Mandarin"):

        language_codes = {
            "Taishanese": 0,
            "IPA": 1,
            "Cantonese": 2,
            "Mandarin": 3,
            "English": 4,
        }

        with webdriver.Chrome(Path.cwd().joinpath("chromedriver")) as driver:

            def search():
                site = (
                    "https://www.stephen-li.com/"
                    "TaishaneseVocabulary/Taishanese.html"
                )
                title_keyword = "Taishanese"
                
                # Open and verify site
                driver.get(site)
                assert title_keyword in driver.title

                # Select language for search
                driver.switch_to.frame("menu")
                language_selector = Select(driver.find_element_by_name("Select1"))
                language_selector.select_by_index((language_codes[language]))

                # Input and search for term
                search_box = driver.find_element_by_name("data")
                search_box.clear()
                search_box.send_keys(word)
                search_box.send_keys(Keys.RETURN)

                # Switch to frame containing search results
                driver.switch_to.default_content()
                driver.switch_to.frame("content")

            def scrape():
                soundclip_url = driver.find_element_by_xpath(
                    "//a[@target='sound']").get_attribute("href")
                results = driver.find_element_by_xpath(
                    "/html/body").text.splitlines()
                entry = results[2]

                print(f"Searched for {word}, found {entry}")

                self.scraped_results[f"{word}"] = (f"{entry}",
                                                    f"{soundclip_url}")

            for word in words:
                search()

                try:
                    scrape()
                except Exception:
                    print(f"No entry found for {word}!")
                    self.failed_count += 1
                    self.failed_entries.append(word)

        print(f"There were {self.failed_count} words missing a definition,"
                f"and they were:\n{self.failed_entries}")

    def import_vocab_list(self, file):

        with open(Path.cwd().joinpath(file), "r") as source:
            results = [line.strip() for line in source]
            return results

    def scrape_hsk(self, hsk_level):

        levels = {
            1: "HSK1.txt",
            2: "HSK2.txt",
            3: "HSK3.txt",
            4: "HSK4.txt",
            5: "HSK5.txt",
            6: "HSK6.txt",
            }

        if hsk_level == 0 or hsk_level == "all":
            for level in levels.values():
                self.search_and_scrape(self.import_vocab_list(level))
        else:
            self.search_and_scrape(self.import_vocab_list(levels[hsk_level]))

    def export_entries(self, filename="scraped_results", extension="txt"):

        with open(Path.cwd().joinpath(f"{filename}.{extension}"),
             "a+") as file:

            def write_entry(word, definition):
                if extension == "txt":
                    file.write(f"{word} : {definition}\n")
                elif extension == "csv":
                    writer = csv.writer(file, delimiter=',', quotechar='"',
                                        quoting=csv.QUOTE_MINIMAL)
                    writer.writerow([f"{word}", f"{definition}"])

            for key, value in self.scraped_results.items():
                write_entry(key, value[0])

    def export_audio(self, folder_name="audio"):
        audio_dir = Path.cwd().joinpath(folder_name)
        if not audio_dir.exists():
            audio_dir.mkdir()

        for word, results in self.scraped_results.items():
                url = results[1]
                filepath = audio_dir.joinpath(f"{word}.mp3")
                if not filepath.exists():
                    urlretrieve(url, filepath)

    def print_results(self):
        for key, value in self.scraped_results.items():
            print(f"TERM: {key} DEF: {value[0]} CLIP: {value[1]}")


def main():
    scraper = TaishaneseScraper()
    scraper.scrape_hsk('all')
    scraper.export_entries(extension='txt')
    scraper.export_entries(extension='csv')
    scraper.export_audio()


if __name__ == '__main__':
    ...
    # main()
