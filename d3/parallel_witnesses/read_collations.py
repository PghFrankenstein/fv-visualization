import json
import re
from glob import glob
from lxml import etree
from difflib import SequenceMatcher
from itertools import groupby
from operator import itemgetter
import math

# Read and join all collation chunks
collation_path = "../../../fv-data/variorum-chunks-tws/*.xml"
collation_chunks = glob(collation_path)
sorted_collation_chunks = sorted(collation_chunks, key = lambda x: int(re.search(r"_C(\d+)", x).groups()[0]))

text_strings = []
chunk_pos = {
    "f1818": [0],
    "f1823": [0],
    "f1831": [0],
    "fThomas": [0]
}
for f in sorted_collation_chunks:
    chunk_text = etree.parse(f).getroot().xpath("//text()")
    for i, ct in enumerate(chunk_text):
        if re.search(r"\n\s+$", ct) is None:
            if ct.is_text:
                # Pull seg ID
                text_ele = ct.getparent().get(
                    "{http://www.w3.org/XML/1998/namespace}id"
                )
            elif ct.is_tail:
                # Suffixed seg ID
                try:
                    text_ele = (
                        ct.getparent().get("{http://www.w3.org/XML/1998/namespace}id")
                        + "_tail"
                    )
                except:
                    continue
            if text_ele is not None:
                chunkname = re.search(r"_(C\d+)", f).groups()[0]
                wit = "f" + re.search(r"f([A-Za-z0-9]+)?_", f).groups()[0]
                text_obj = {
                    "witness": wit,
                    "chunk": chunkname,
                    "index": i,
                    "start_pos": sum(chunk_pos[wit]),
                    "seg": text_ele.split("-")[0],
                    "content": str(ct),
                }
                chunk_pos[wit].append(len(str(ct)))
                text_strings.append(text_obj)
text_strings.sort(key=itemgetter("seg"))
witnesses = ["f1818", "f1823", "f1831", "fThomas"]
seg_texts = []
for key, rawkeydicts in groupby(text_strings, key=itemgetter("seg")):
    keydicts = [dict(d) for d in rawkeydicts]
    for source_wit in witnesses:
        try:
            source_text = [
                t["content"] for t in keydicts if t["witness"] == source_wit
            ][0]
            source_index = [
                t["index"] for t in keydicts if t["witness"] == source_wit][0]
            source_pos = [
                t["start_pos"] for t in keydicts if t["witness"] == source_wit][0]
        except:
            source_text = ""
            source_index = None
            source_pos = None
        for target_wit in witnesses:
            try:
                target_text = [
                    a["content"] for a in keydicts if a["witness"] == target_wit
                ][0]
                target_index = [
                    a["index"] for a in keydicts if a["witness"] == target_wit
                ][0]
                target_pos = [
                    a["start_pos"] for a in keydicts if a["witness"] == target_wit
                ][0]
            except:
                target_text = ""
                target_index = None
                target_pos = None
            if source_text is not None and target_text is not None:
                seqer = SequenceMatcher(lambda x: x == " ", source_text, target_text)
                diff_ops = seqer.get_opcodes()
                formatted_diff_ops = [
                    {"tag": tag, "a1": a1, "a2": a2, "b1": b1, "b2": b2}
                    for tag, a1, a2, b1, b2 in diff_ops
                ]
                diff_additions = sum(
                    [
                        o["b2"] - o["b1"]
                        for o in formatted_diff_ops
                        if o["tag"] in ["insert"]
                    ]
                ) + sum (
                    [
                        o["b2"] - o["b1"]
                        for o in formatted_diff_ops
                        if o["tag"] in ["replace"]
                    ]
                )
                diff_replacements = sum(
                    [
                        (o["a2"] - o["a1"])
                        for o in formatted_diff_ops
                        if o["tag"] in ["replace"]
                    ]
                )
                diff_deletions = sum(
                    [
                        o["a2"] - o["a1"]
                        for o in formatted_diff_ops
                        if o["tag"] in ["delete"]
                    ]
                ) + sum(
                    [
                        o["a2"] - o["a1"]
                        for o in formatted_diff_ops
                        if o["tag"] in ["replace"]
                    ]
                )
                diff_stats = {
                    "additions": math.log(diff_additions + 1),
                    "deletions": math.log(diff_deletions + 1),
                    "replacements": math.log(diff_replacements + 1),
                    "balance": (diff_additions - diff_deletions)
                    / (len(target_text) + len(source_text) + 1),
                    "aggregate": diff_additions + diff_deletions + diff_replacements
                }
            else:
                diff_ops = None
                diff_stats = {"additions": 0, "deletions": 0, "replacements": 0, "balance": 0, "aggregate": 0}

            res = {
                "seg": key,
                "source_witness": source_wit,
                "source_text": source_text,
                "source_index": source_index,
                "source_pos": source_pos,
                "target_witness": target_wit,
                "target_text": target_text,
                "target_index": target_index,
                "target_pos": target_pos,
                "diff_ops": formatted_diff_ops,
                "diff_stats": diff_stats,
            }
            seg_texts.append(res)
seg_texts.sort(key=itemgetter("seg"))
final_output = {"segs": [], "stats": {}}
addition_ranges = []
deletion_ranges = []
replacement_ranges = []
balance_ranges = []
aggregate_ranges = []
nchar_ranges = []
for seg, segdicts in groupby(seg_texts, key=itemgetter("seg")):
    res = {"seg": seg, "witnesses": []}
    segdicts = [dict(d) for d in segdicts]
    for source, sourcedicts in groupby(segdicts, key=itemgetter("source_witness")):
        sourcedicts = [dict(d) for d in sourcedicts]
        target_diffs = []
        for d in sourcedicts:
            addition_ranges.append(d["diff_stats"]["additions"])
            deletion_ranges.append(d["diff_stats"]["deletions"])
            replacement_ranges.append(d["diff_stats"]["replacements"])
            balance_ranges.append(d["diff_stats"]["balance"])
            aggregate_ranges.append(d["diff_stats"]["aggregate"])
            target_diffs.append({
                "wit": d["target_witness"],
                "ops": d["diff_ops"],
                "stats": d["diff_stats"]
            })

        wit_content = sourcedicts[0]["source_text"]
        wit_index = sourcedicts[0]["source_index"]
        if wit_content is not None:
            content_nchar = len(wit_content)
            nchar_ranges.append(content_nchar)
        else:
            content_nchar = None
        res["witnesses"].append({
            "wit": source,
            "index": wit_index,
            "text": {"content": wit_content, "nchar": content_nchar},
            "diffs": target_diffs,
        })
    final_output["segs"].append(res)

final_output["stats"]["addition"] = {
    "min": min([a for a in addition_ranges if a is not None]),
    "max": max([a for a in addition_ranges if a is not None]),
}


final_output["stats"]["deletion"] = {
    "min": min([a for a in deletion_ranges if a is not None]),
    "max": max([a for a in deletion_ranges if a is not None]),
}

final_output["stats"]["replacements"] = {
    "min": min([a for a in replacement_ranges if a is not None]),
    "max": max([a for a in replacement_ranges if a is not None]),
}

final_output["stats"]["balance"] = {
    "min": min([a for a in balance_ranges if a is not None]),
    "max": max([a for a in balance_ranges if a is not None]),
}

final_output["stats"]["aggregate"] = {
    "min": min([a for a in aggregate_ranges if a is not None]),
    "max": max([a for a in aggregate_ranges if a is not None]),
}

final_output["stats"]["nchar"] = {
    "min": min([a for a in nchar_ranges if a is not None]),
    "max": max([a for a in nchar_ranges if a is not None]),
}

with open("diffs.json", "w") as o:
    json.dump(final_output, o, indent=2)

with open("out.json", "w") as o:
  json.dump(seg_texts, o, indent = 2)
