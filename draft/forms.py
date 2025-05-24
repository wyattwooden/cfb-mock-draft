# draft/forms.py
from django import forms

TEAM_CHOICES = [(i, str(i)) for i in range(4, 33)]

class MockDraftSettingsForm(forms.Form):
    num_teams = forms.ChoiceField(choices=TEAM_CHOICES, initial=12, label="")

    draft_slot = forms.ChoiceField(choices=[], label="Your Draft Slot")

    qb = forms.IntegerField(min_value=0, max_value=4, initial=1)
    rb = forms.IntegerField(min_value=0, max_value=10, initial=2)
    wr = forms.IntegerField(min_value=0, max_value=10, initial=2)
    te = forms.IntegerField(min_value=0, max_value=4, initial=1)
    flex = forms.IntegerField(min_value=0, max_value=10, initial=1)
    k = forms.IntegerField(min_value=0, max_value=4, initial=1)
    dst = forms.IntegerField(min_value=0, max_value=4, initial=1)
    bench = forms.IntegerField(min_value=0, max_value=20, initial=6)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically set draft_slot choices based on the selected num_teams
        data = self.data or self.initial
        try:
            num_teams = int(data.get("num_teams", 12))
        except (TypeError, ValueError):
            num_teams = 12

        self.fields["draft_slot"].choices = [(i, f"Pick {i}") for i in range(1, num_teams + 1)]

    def clean(self):
        cleaned_data = super().clean()
        try:
            num_teams = int(cleaned_data.get("num_teams", 12))
            draft_slot = int(cleaned_data.get("draft_slot", 1))
            if not (1 <= draft_slot <= num_teams):
                self.add_error("draft_slot", f"Pick must be between 1 and {num_teams}.")
        except (ValueError, TypeError):
            self.add_error("draft_slot", "Invalid draft slot.")

        # Automatically calculate total number of rounds
        cleaned_data["num_rounds"] = sum([
            cleaned_data.get("qb", 0),
            cleaned_data.get("rb", 0),
            cleaned_data.get("wr", 0),
            cleaned_data.get("te", 0),
            cleaned_data.get("flex", 0),
            cleaned_data.get("k", 0),
            cleaned_data.get("dst", 0),
            cleaned_data.get("bench", 0),
        ])

        return cleaned_data
