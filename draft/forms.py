# draft/forms.py
from django import forms

TEAM_CHOICES = [(i, str(i)) for i in range(4, 33)]

class MockDraftSettingsForm(forms.Form):
    num_teams = forms.ChoiceField(choices=TEAM_CHOICES, initial=12, label="")
    
    qb = forms.IntegerField(min_value=0, max_value=4, initial=1)
    rb = forms.IntegerField(min_value=0, max_value=10, initial=2)
    wr = forms.IntegerField(min_value=0, max_value=10, initial=2)
    te = forms.IntegerField(min_value=0, max_value=4, initial=1)
    flex = forms.IntegerField(min_value=0, max_value=10, initial=1)
    k = forms.IntegerField(min_value=0, max_value=4, initial=1)
    dst = forms.IntegerField(min_value=0, max_value=4, initial=1)
    bench = forms.IntegerField(min_value=0, max_value=20, initial=4)

