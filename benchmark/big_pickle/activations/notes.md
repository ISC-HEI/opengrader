# Analysis

As we can see, not bad for a start ~80% precision. Clearly not sufficient.

I have seen that the model is good at incremental rubric

ex: 
"a" correct         + 0.1
"b" correct         + 0.2
"c" correct         + 0.3
                    total = 0.5

And not at OR rubrics

ex:
"a" correct         + 0.1
"a + b" correct     + 0.3
"a + b + c" correct + 0.5
                    total = 0.9 -> should not activate multiple at the same time !

Will try to add the value of the rubrics in the llm prompt, and tell him the maximum point to be attribued to try to avoid this ?
