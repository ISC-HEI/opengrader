# Reading + correcting scans

Tried having `Big pickle` as main agent, and `Gemini 2.5 flash lite` as a document reader -> translating the document into text does not work well at all.
Many errors, many hallucination.

I think the main agent may need to be able to read files directly, because transmitting written schema in pure text is not good...


When trying to send pdf to a model -> put this in the opencode provider config : `"npm": "@openrouter/ai-sdk-provider",` else, the pdf won't be read


Big fail for gpt 4o... can't read


gtp 5 nano seems to not know how to use skills :)))


## Notes 16.03

showcase du projet :
- Pour mon portofolio et pour hes
- Technical paper ?
- Screencast 
- Blogpost
- ...
- Demander à PA quel est le meilleur moyen -> Fait, en attente

format unifié -> plusieurs solution par questions

Installation windows ???

Focus ->
Précision correction -> créer benchmark avec l'exam 2025 de .mbz
from gradescope -> export rubrics and correction
use rubric for correction



Then, find a way to evaluate -> either blind judge or delta between rubrics

Test with more context (for example module description) -> only question 1 and 6 



Une fois qu'on a l'évluation totale -> donner tout à un autre LLM (mbz prompt + sortie évaluation), on prend un gros modèle et on lui demande ce qu'il s'est passé

Après excel -> deuxième exam avec stat détaillées

tout à la fin-> Typst comme template
