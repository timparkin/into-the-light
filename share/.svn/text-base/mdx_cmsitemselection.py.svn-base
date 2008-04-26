
import markdown
from cms.widgets.itemselection import ItemSelection

def getItemSelectionRepr(selectionString):
    return '<div style="border:1px solid red;padding:10px;">%s</div>'%(selectionString.replace(';','\n'))

def getItemSelection(encodedItemsel):
    itemsel = ItemSelection.fromString(str(encodedItemsel))
    if itemsel.id:
        # Individual item
        htmlFragment = """
        <n:invisible n:data="cmsitemselection %(itemsel)s" n:render="cmsitemselection %(itemsel)s" />
        """%{'itemsel': encodedItemsel}
    elif itemsel.paging:
        # List with paging tags
        htmlFragment = """
        <n:invisible n:data="cmsitemselection %(itemsel)s" n:render="paging %(itemsPerPage)s" >
          <n:invisible n:pattern="item" n:render="cmsitemselection %(itemsel)s" />
        </n:invisible>
        <n:invisible n:render="fragment paging_controls" />
        """%{'itemsel': encodedItemsel, 'itemsPerPage':itemsel.paging}
    else:
        # List without paging
        htmlFragment = """
        <n:invisible n:data="cmsitemselection %(itemsel)s" n:render="sequence" >
          <n:invisible n:pattern="item" n:render="cmsitemselection %(itemsel)s" />
        </n:invisible>
        """%{'itemsel': encodedItemsel}
    return htmlFragment

class CMSItemSelection(markdown.Preprocessor) :
    
    def __init__(self,context):
        self.context=context[0] 
    
    def run(self, lines) :
        for i in range(len(lines)) :
            if lines[i].startswith('cmsitemselection://') :
                if self.context == 'admin':
                    lines[i] = getItemSelectionRepr('CMS Items Matching: %s'%lines[i][19:])
                else:
                    lines[i] = getItemSelection(lines[i][19:])
                    

        return lines


class CMSItemSelectionExtension (markdown.Extension):
    
    def __init__ (self, configs) :

        self.config = {'context' :
                       ["public",
                        "Which mode to convert in. In admin mode, item selectors just show a placeholder"]}
        for key, value in configs :
            self.setConfig(key, value)
    

    def extendMarkdown(self, md, md_globals):
        self.md = md
        # inline patterns
        index = md.preprocessors.index(md_globals['REFERENCE_PREPROCESSOR'])
        preprocessor = CMSItemSelection(context=self.config['context'])
        preprocessor.md = md
        md.preprocessors.insert(index,preprocessor)
    
def makeExtension(configs=None) :
    return CMSItemSelectionExtension(configs=configs) 