from django import forms

class HeritageSiteFilterForm(forms.Form):
    """Heritage site filter form"""
    search = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter name or country',
            'class': 'form-control'
        })
    )
    
    country = forms.CharField(
        required=False,
        label='Country',
        widget=forms.TextInput(attrs={
            'placeholder': 'Country name',
            'class': 'form-control'
        })
    )
    
    category = forms.ChoiceField(
        required=False,
        label='Category',
        choices=[
            ('', 'All'),
            ('Cultural', 'Cultural Heritage'),
            ('Natural', 'Natural Heritage'),
            ('Mixed', 'Mixed Heritage'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
