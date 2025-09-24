# forms.py
from django import forms
from .models import Book
from django.contrib.auth.models import User

class BookSearchForm(forms.Form):
    q = forms.CharField(label="Search books (title)", required=False)

class IssueForm(forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.all())
    # For staff only: select a user to issue to. Not required for normal users.
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)

class ReturnForm(forms.Form):
    # hidden field just to confirm transaction id in POST
    transaction_id = forms.IntegerField(widget=forms.HiddenInput)
