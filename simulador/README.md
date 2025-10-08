# Documentação do Aplicativo Django: simulador

## 1. Visão Geral

O aplicativo `simulador` tem como funcionalidade servir uma interface web para o projeto `APP Simulador`. Este por sua vez é uma aplicação móvel desenvolvida com Expo, focada na simulação de juros de vendas. Ele utiliza o roteamento baseado em arquivos do Expo Router e inclui componentes para entrada de dados financeiros, seleção de equipamentos e geração de PDFs.

## 2. Views

Sua view oferece apenas um roteamento para templates/simulador que está na seguinte árvore:

```
templates/
├── _sitemap.html
├── +not-found.html
├── index.html
├── simulador/
│   ├── index.html
```

Como dito ele oferece apenas uma interface web então os arquivos são gerados pelo `npx expo export -p web`

## 3. Static

Por ser um sistema desenvolvido em expo é gerado o arquivo JS que está na pasta static deste projeto.

## 4. Observação

- Tem dois arquivos index.html pelo fato de ter ocorrido algum erro na hora do desenvolvimento. Esta é uma observação para futuras correções
- Se precisar de detalhes como funciona procure pela documentação do aplicativo onde está sendo explicado o necessário.

