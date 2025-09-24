# forms.py
from django import forms
from .models import Book, Member
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


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['code_no', 'title', 'author', 'category', 'isbn', 'total_copies', 'available_copies']

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'is_staff', 'is_active']

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data["password"]:
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['user', 'phone', 'adhaar', 'membership_type', 'membership_start', 'membership_end']
