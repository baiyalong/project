from django import forms

class HeritageSiteFilterForm(forms.Form):
    """筛选表单"""
    search = forms.CharField(
        required=False,
        label='搜索',
        widget=forms.TextInput(attrs={
            'placeholder': '输入名称或国家',
            'class': 'form-control'
        })
    )
    
    country = forms.CharField(
        required=False,
        label='国家',
        widget=forms.TextInput(attrs={
            'placeholder': '国家名称',
            'class': 'form-control'
        })
    )
    
    category = forms.ChoiceField(
        required=False,
        label='类型',
        choices=[
            ('', '全部'),
            ('Cultural', '文化遗产'),
            ('Natural', '自然遗产'),
            ('Mixed', '混合遗产'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
