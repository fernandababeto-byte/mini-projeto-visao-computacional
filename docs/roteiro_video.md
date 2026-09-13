# Roteiro de vídeo - duração aproximada: 4 min 45 s

Grave com **rosto visível e boa iluminação**. Pode ser na vertical ou horizontal. Deixe o terminal, a pasta do projeto, o CSV e `reports/comparativo.png` abertos para evitar pausas. Troque qualquer fala sobre publicação pela URL real quando o repositório estiver disponível.

| Tempo | Tela | Fala sugerida |
| --- | --- | --- |
| 0:00–0:35 | Rosto + README | "Meu projeto prepara imagens de peças fundidas para uma futura etapa de aprendizado de máquina. Ele não decide se uma peça tem defeito: destaca contornos e ranhuras, processa várias imagens e guarda os resultados de forma padronizada." |
| 0:35–1:35 | Pastas `raw_images`, terminal e `reports/comparativo.png` | "Recebi 1.300 imagens, em duas pastas. Criei um ambiente virtual e instalei as dependências do `requirements.txt`. Primeiro extraio o ZIP com `python prepare_dataset.py --archive ...`; depois executo `python preprocess.py`. O sistema descobre os arquivos automaticamente. Aqui está uma amostra do original, cinza, suavização, Otsu, máscara, bordas e saída 256 por 256." Rode antes `python preprocess.py --limit-per-class 2 --output reports/demo_output --report reports/demo.csv`, se desejar demonstrar a execução ao vivo. |
| 1:35–2:25 | Código `preprocess.py`, comparativo | "Converto BGR para cinza, aplico blur gaussiano, binarizo regiões escuras com Otsu, separo a peça do fundo com GrabCut e elipse, refino com erosão/dilatação e destaco as bordas com Canny. O fundo é removido e preservo os tons de cinza da peça." Mostre rapidamente máscaras e bordas. |
| 2:25–3:05 | README e estrutura de pastas | "Planejei as tarefas em sprints: configurar Git e o ambiente; organizar e ler os dados; criar as etapas base; segmentar e detectar bordas; refinar a máscara e padronizar; testar, documentar e apresentar. Os dados e resultados não entram no GitHub, apenas código e documentação." |
| 3:05–3:40 | Terminal com `git branch -a` e `git log --oneline --graph --all` | "Criei `main` para a versão consolidada, `development` para integração, `feature/leitura-lote` para a extração, `feature/pre-processamento-base` para cinza/blur/Otsu, `feature/morfologia-bordas` para máscara/morfologia/Canny e `docs/documentacao` para explicar e apresentar. Cada funcionalidade teve commit próprio e foi integrada por merge." |
| 3:40–4:30 | CSV e preview | "Uma melhoria futura é validar manualmente as máscaras, sobretudo quando aparecer `fallback_circulo_verificar` no CSV; também posso preservar imagens maiores para defeitos muito finos e testar parâmetros em dados anotados. As bordas indicam estrutura, não equivalem a uma classificação de defeitos." |
| 4:30–4:45 | Rosto + pasta final | "Estes são os arquivos de código, os testes e a demonstração visual. O README mostra como repetir a execução." |

Antes de enviar: veja o vídeo inteiro; confirme som, rosto, iluminação, duração **até cinco minutos**, leitura da tela e cobertura dos cinco itens do enunciado. Compartilhe o vídeo no Drive em modo **qualquer pessoa com o link: leitor**; inclua o link na entrega e, se quiser, no README do GitHub.

