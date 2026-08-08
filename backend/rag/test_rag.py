from rag_service import ask_rag


question = "When is the Dance Competition?"


result = ask_rag(
    question
)


print("\n==============================")
print("QUESTION")
print("==============================")

print(question)


print("\n==============================")
print("ANSWER")
print("==============================")

print(
    result["response"]
)


print("\n==============================")
print("SOURCES")
print("==============================")

for source in result["sources"]:

    print(
        source
    )