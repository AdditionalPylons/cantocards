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