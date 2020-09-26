from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from pathlib import Path
from typing import List


class TaishaneseScraper():

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

        with webdriver.Chrome(Path.cwd().joinpath("chromedriver")) as driver, \
             open(Path.cwd().joinpath("scraped_results.txt"), "a+") as export_file:
            failed_count = 0
            failed_entries = []
            for word in self.words:
                driver.get("https://www.stephen-li.com/"
                           "TaishaneseVocabulary/Taishanese.html")
                assert "Taishanese" in driver.title
                driver.switch_to.frame("menu")
                button = Select(driver.find_element_by_name("Select1"))
                button.select_by_index((language_codes[self.language]))
                elem = driver.find_element_by_name("data")
                elem.clear()
                elem.send_keys(word)
                elem.send_keys(Keys.RETURN)
                driver.switch_to.default_content()
                driver.switch_to.frame("content")

                try:
                    soundclip = driver.find_element_by_xpath(
                        "//a[@target='sound']").get_attribute("href")
                    results = driver.find_element_by_xpath(
                        "/html/body").text.splitlines()
                    entry = results[2]
                    print(f"Searched for {word}, found {entry}")
                    print(f"Audio file available at: {soundclip}")
                    export_file.write(f"{word} : {entry}\n")
                except Exception:
                    print(f"No entry found for {word}!")
                    failed_count += 1
                    failed_entries.append(word)
            export_file.write(f"There were {failed_count} words missing "
                              "a definition, and they were: {failed_entries}")

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


scraper = TaishaneseScraper()
scraper.scrape_hsk(1)
