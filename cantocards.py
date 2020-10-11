from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from pathlib import Path
from typing import List

import csv


def main():
    scraper = TaishaneseScraper()
    scraper.scrape_hsk(1)
    scraper.export_entries()


class TaishaneseScraper():

    scraped_results = {}
    failed_count = 0
    failed_entries = []

    def search_and_scrape(self, words: List, language="Mandarin"):
        self.words = words
        self.language = language

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
                language_selector.select_by_index((language_codes[self.language]))

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

            for word in self.words:
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
        self.file = file

        with open(Path.cwd().joinpath(file), "r") as source:
            results = [line.strip() for line in source]
            return results

    def scrape_hsk(self, hsk_level):
        self.hsk_level = hsk_level

        levels = {
            1: "HSK1.txt",
            2: "HSK2.txt",
            3: "HSK3.txt",
            4: "HSK4.txt",
            5: "HSK5.txt",
            6: "HSK6.txt",
            }

        if self.hsk_level == 0 or self.hsk_level == "all":
            for level in levels.values():
                self.search_and_scrape(self.import_vocab_list(level))
        else:
            self.search_and_scrape(self.import_vocab_list(levels[hsk_level]))

    def export_entries(self, filename="scraped_results", extension="txt"):
        self.filename = filename
        self.extension = extension

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

    def print_results(self):
        for key, value in self.scraped_results.items():
            print(f"TERM: {key} DEF: {value[0]} CLIP: {value[1]}")


class FlashCard():
    def __init__(self, term, definition, soundclip=None):
        self.term = term
        self.definition = definition
        self.soundclip = soundclip

    def __str__(self):
        return f"Term = {self.term}\nDefinition = {self.definition}"

    def test_term(self):
        answer = input(f"What is the meaning of {self.term}? ")
        if answer.casefold() == self.definition.casefold():
            print("Correct!")
        else:
            print("Wrong.")

    def test_definition(self):
        answer = input(f"How do you say {self.definition}? ")
        if answer.casefold() == self.term.casefold():
            print("Correct!")
        else:
            print("Wrong.")


if __name__ == '__main__':
    main()
