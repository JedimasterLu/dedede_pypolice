import hanlp
from hanlp_common.document import Document

class NLP:
    def __init__(self):
        self.tok = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)
        self.con = hanlp.load('CTB9_CON_FULL_TAG_ELECTRA_SMALL')
        self.pos = hanlp.load(hanlp.pretrained.pos.CTB9_POS_ELECTRA_SMALL)
        self.nlp = hanlp.pipeline() \
            .append(self.tok, output_key='tok') \
            .append(self.pos, input_key='tok', output_key='pos') \
            .append(self.con, input_key='tok', output_key='con') \
            .append(self.merge_pos_into_con, input_key='*')

    def merge_pos_into_con(self, doc:Document):
        flat = isinstance(doc['pos'][0], str)
        if flat:
            doc = Document((k, [v]) for k, v in doc.items())
        for tree, tags in zip(doc['con'], doc['pos']):
            offset = 0
            for subtree in tree.subtrees(lambda t: t.height() == 2):
                tag = subtree.label()
                if tag == '_':
                    subtree.set_label(tags[offset])
                offset += 1
        if flat:
            doc = doc.squeeze()
        return doc
    
    def process(self, text:str) -> Document:
        return self.nlp(text)

'''
nlp = NLP()
doc = nlp.process('今天我去厦门玩了。我吃了很多的冰淇凌。我玩得很开心。')
print(doc)
doc.pretty_print()
'''