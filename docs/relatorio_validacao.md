# Relatório de validação final

Validação realizada em 13/09/2026 com Python 3.12, NumPy 1.26.4 e OpenCV Headless 4.10.0.84.

## Resultado da execução completa

| Verificação | Resultado |
| --- | ---: |
| Imagens encontradas | 1.300 |
| `def_front` | 781 |
| `ok_front` | 519 |
| Processadas com sucesso | 1.300 |
| Falhas | 0 |
| Saídas PNG únicas | 1.300 |
| PNGs inválidos | 0 |
| Formato conferido | 256 × 256, `uint8`, um canal |
| Segmentação `grabcut_elipse` | 1.293 |
| Segmentação `fallback_circulo_verificar` | 7 |

As sete alternativas conservadoras foram inspecionadas visualmente. Em todas, o círculo central preservou a peça completa e o realce das estruturas internas. O caso `cast_ok_0_7014.jpeg` motivou uma correção: o primeiro ajuste selecionava apenas o anel interno; após elevar a cobertura mínima aceita, ele foi encaminhado ao fallback e reprocessado corretamente.

## Métricas do lote

| Métrica | Mínimo | Mediana | Média | Máximo |
| --- | ---: | ---: | ---: | ---: |
| Limiar de Otsu | 92,0 | 109,0 | 117,5785 | 169,0 |
| Cobertura da máscara | 0,3416 | 0,5801 | 0,5798 | 0,7822 |
| Cobertura das bordas | 0,0384 | 0,0675 | 0,0680 | 0,1013 |

O relatório bruto da execução é `reports/execucao.csv`, gerado localmente e ignorado pelo Git para não publicar arquivos derivados. SHA-256 conferido: `4e7b72119b46f14716fa67357559cc4023720bd3076745a71b98a0688b08c5a2`.

## Testes automatizados

Comando: `python -m unittest discover -s tests -v`.

Resultado: **5 testes aprovados**. Eles cobrem:

1. extração segura apenas das duas classes esperadas e execução repetível;
2. saída padronizada com preservação de bordas internas;
3. processamento das duas classes e registro de arquivo corrompido sem travar o lote;
4. rejeição de uma pasta de saída localizada dentro da entrada;
5. uso do fallback marcado para revisão quando a segmentação não é confiável.

Também passaram a compilação dos quatro módulos Python e a verificação de espaços/erros do diff do Git.
