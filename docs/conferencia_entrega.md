# Conferência objetiva da rubrica

| Critério | Evidência pronta para avaliação | Etapa final |
| --- | --- | --- |
| 1. Vídeo (2,0) | `docs/roteiro_video.md` cobre as cinco perguntas com demonstração cronometrada | Gravar o próprio rosto, mostrar a execução e compartilhar o vídeo em modo leitor |
| 2. Branches e commits (1,0) | `main`, `development`, três branches `feature/` e `docs/documentacao`, com commits e merges distintos | Publicar **todas** as branches no GitHub após conectar a conta |
| 3. Organização e README (1,0) | `.gitignore`, `README.md`, scripts, testes e pastas de entrada/saída | Conferir o repositório público/compartilhável e o link do README no Drive |
| 4. Lote (1,0) | `preprocess.py: image_paths, process_batch`; ignora arquivos não-imagem e relata corrupção | Mostrar duas classes e relatório no vídeo |
| 5. Conversão (1,0) | `cv2.cvtColor(..., COLOR_BGR2GRAY)` | Mostrar estágio "cinza" no comparativo |
| 6. Blur (1,0) | `cv2.GaussianBlur(..., (5, 5), 0.9)` antes de Otsu/Canny | Mostrar estágio "suavizada" |
| 7. Limiarização (1,0) | Otsu binariza sulcos escuros; GrabCut + elipse isolam a peça do fundo variável | Mostrar Otsu e máscara externa, explicar por que ambos são necessários |
| 8. Morfologia (1,0) | Erosão/dilatação com elemento elíptico 3 × 3, remoção de artefatos | Mostrar a máscara limpa |
| 9. Bordas (1,0) | Canny e gradiente da região escura, limitados à peça | Mostrar bordas e saída final, inclusive uma amostra `def_front` |

**Prazo indicado no enunciado e no AVA:** 14/09/2026 às 22h. Envie no AVA os links efetivos do README e vídeo no Google Drive, com permissão de leitor para qualquer pessoa com o link. A nota depende da avaliação da instituição; esta lista ajuda a evitar itens esquecidos, não é garantia de nota.

