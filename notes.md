# Reading + correcting scans

Tried having `Big pickle` as main agent, and `Gemini 2.5 flash lite` as a document reader -> translating the document into text does not work well at all.
Many errors, many hallucination.

I think the main agent may need to be able to read files directly, because transmitting written schema in pure text is not good...


When trying to send pdf to a model -> put this in the opencode provider config : `"npm": "@openrouter/ai-sdk-provider",` else, the pdf won't be read


Big fail for gpt 4o... can't read


gtp 5 nano seems to not know how to use skills :)))
