from __future__ import annotations

from django import forms

EXTENSOES_ACEITAS = (".csv", ".xlsx")


class UploadArquivoForm(forms.Form):
    arquivo = forms.FileField(
        label="Arquivo (CSV ou XLSX)",
        help_text="Colunas esperadas: nome, nome_fantasia, cnpj, tipo_organizacao, municipio, uf, "
        "setor_economico, porte, ano_fundacao, site, ativa, data_entrada_ecossistema, "
        "nome_contato, email_contato, telefone_contato, cargo_contato.",
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        nome = arquivo.name.lower()
        if not nome.endswith(EXTENSOES_ACEITAS):
            raise forms.ValidationError("Envie um arquivo .csv ou .xlsx.")
        return arquivo
