# dump_twl06.py

import twl

OUTPUT_FILE = "twl06.txt"

def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for word in twl.iterator():
            f.write(word + "\n")
    print(f"Wrote {len(list(twl.iterator()))} words to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
