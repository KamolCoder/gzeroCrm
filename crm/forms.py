from django import forms
from django.db.models.functions import TruncDate
from .models import Client, Order, AbonementBuyList
from django.contrib.auth.forms import AuthenticationForm


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'surname', 'phone', 'email', 'telegram_id',
                  'username', 'image', 'comment', 'docs', 'added_user', 'discount']
        widgets = {'added_user': forms.HiddenInput(),
                   'name': forms.TextInput(attrs={
                       'class': 'form-control',
                       'placeholder': 'Имя'
                   }),
                   'surname': forms.TextInput(attrs={
                       'class': 'form-control',
                       'placeholder': 'Фамилия'
                   }),
                   'telegram_id': forms.Textarea(attrs={
                       'class': 'form-control  p-2',
                       "id": "output",
                       "rows": "1",
                       'placeholder': 'Нажмите для получение ИД',
                       "readonly": "readonly",
                       'hidden':'hidden'
                   }),
                   'phone': forms.TextInput(attrs={
                       'placeholder': '+998',
                       'class': 'form-control'
                   }),
                   'filial': forms.Select(attrs={
                       'class': 'form-control ',
                       'placeholder': 'Филиал'
                   }),
                   'email': forms.EmailInput(attrs={
                       'class': 'form-control ',
                       'placeholder': 'Email'
                   }),
                   'docs': forms.ClearableFileInput(attrs={
                       'class': 'form-control'

                   }),
                   'image': forms.FileInput(attrs={
                       'class': 'form-control '
                   }),
                   'comment': forms.TextInput(attrs={
                       'class': 'form-control ',
                       'placeholder': "необязательно"
                   }),
                   'discount': forms.NumberInput(attrs={
                       'class': 'form-control ',
                   })
                   }


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={"class": "form-control",
               "Placeholder": "Username"}), label='')
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control',
               "autocomplete": "current-password",
               'placeholder': 'Password'}), label='')


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['client', 'filial', "product", 'hour',
                  'order_start', 'order_end', 'payment', 'payment_status', 'status', 'discount']
        widgets = {
            'filial': forms.Select(
                attrs={'class': 'form-control', 'id': "filialSelect", 'onchange': "updateTitleOptions()"}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'product': forms.Select(
                attrs={'class': 'form-control', 'id': "titleSelect", 'onchange': "updateHourOptions()"}),
            'hour': forms.Select(attrs={'class': 'form-control', 'id': "hourSelect"}),
            # 'comment':forms.Textarea(attrs={'rows':"2", 'class': 'form-control'}),
            'order_start': forms.DateTimeInput(attrs={'type': 'datetime-local', "class": 'form-control'}),
            'order_end': forms.DateTimeInput(
                attrs={'type': 'datetime-local', "class": 'form-control', "readonly": "readonly"}),
            'payment': forms.Select(attrs={'class': 'form-control'}),
            "payment_status": forms.CheckboxInput(attrs={'style': 'width:30px;height:30px;'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', "max": "100"}),

        }

    def clean(self):
        cleaned_data = super().clean()
        dannie = Order.objects.annotate(date=TruncDate("order_start")).filter(is_deleted=False,
                                                                              filial=cleaned_data['filial'],
                                                                              date=cleaned_data["order_start"],
                                                                              product=cleaned_data["product"]).values(
            'product', 'product__category__title', 'order_start', 'order_end')
        t1 = cleaned_data["order_start"]
        t2 = cleaned_data["order_end"]
        lst2 = []
        for i in dannie:
            if not i['product__category__title'] == 'open-space':
                s1, s2 = i['order_start'], i['order_end']
                if t1 > s1 and t1 >= s2 and t2 >= s1 and t2 > s2:
                    lst2.append(True)
                elif t1 < s1 and s2 >= t1 and s1 >= t2 and t2 < s2:
                    lst2.append(True)
                else:
                    lst2.append(False)
            else:
                lst2.append(True)
        if False in lst2:
            raise forms.ValidationError("Это времья уже занято")
        else:
            return cleaned_data


class AbonementForm(forms.ModelForm):
    class Meta:
        model = AbonementBuyList
        fields = ['abonement', 'client', 'subscription_start', 'subscription_end']
        widgets = {
            'abonement': forms.Select(attrs={
                'class': 'form-control',
            }),
            'client': forms.TextInput(attrs={
                "class": 'form-control',
                "readonly": "readonly",
            }),
            'subscription_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'subscription_end': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control', "readonly": "readonly"}),

        }
