#!/usr/bin/env python2

#    4DML Transformation Utility
#
#    (C) 2002-2006 Silas S. Brown (University of Cambridge Computer Laboratory,
#        Cambridge, UK, http://ssb22.user.srcf.net )
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program; see the file COPYING.  If not, write to
#     the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#     Boston, MA 02111-1307, USA.

#!/usr/bin/env python2

# search **** for things that need doing

import xml.parsers.expat, sys
from xml_in import xmlFileToFourspace,xmlStringToFourspace,\
     makePrintable
import edit
from fourspace import listsToPairs
from dimens import scopeDimension,positionDimension
import version

# Put this after all other imports (then the installer can
# compile most modules even if wx can't init at the time)
from wxPython.wx import *

DefaultSize = (540,380)

notShown = xmlStringToFourspace("""<?xml version="1.0"?><NOT_SHOWN>Use View menu</NOT_SHOWN>""")

# ####################################################
# Service routines for the wxWindows library
# ####################################################
def splitPanel(parent,direction):
    panel1 = wxPanel(parent,-1)
    panel2 = wxPanel(parent,-1)
    sizer = wxBoxSizer(direction)
    sizer.Add(panel1,1,wxEXPAND | wxALL, 1)
    sizer.Add(panel2,1,wxEXPAND | wxALL, 1)
    # last param is border width
    parent.SetSizer(sizer)
    parent.SetAutoLayout(true)
    return (panel1, panel2)

def splitSash(parent,direction):
    sash = wxSashLayoutWindow(parent,-1)
    sashSizer = wxBoxSizer(direction)
    panel1 = wxPanel(sash,-1)
    sashSizer.Add(panel1,1,wxEXPAND)
    if direction == wxHORIZONTAL:
        sash.SetSashVisible(wxSASH_RIGHT,1)
    else:
        sash.SetSashVisible(wxSASH_BOTTOM,1)
    sash.SetSizer(sashSizer)
    sash.SetAutoLayout(true)
    class SashDragHandler:
        def handle(self,event):
            wholeSize = self.parent.GetSize()
            oldOtherSize = self.other.GetSize()
            leftSize = event.GetDragRect().GetSize()
            self.sash.SetSize(leftSize)
            if self.direction == wxHORIZONTAL:
                self.other.SetSize((wholeSize.GetWidth() - leftSize.GetWidth(),oldOtherSize.GetHeight()))
                self.other.SetPosition((event.GetDragRect().GetWidth(),self.sash.GetPosition().y))
            else:
                self.other.SetSize((oldOtherSize.GetWidth(),wholeSize.GetHeight()-leftSize.GetHeight()))
                self.other.SetPosition((self.sash.GetPosition().x,event.GetDragRect().GetHeight()))
    handler = SashDragHandler()
    handler.sash = sash
    handler.parent = parent
    handler.direction = direction
    EVT_SASH_DRAGGED(sash, sash.GetId(), handler.handle)
    panel2 = wxPanel(parent,-1)
    handler.other = panel2
    sizer = wxBoxSizer(direction)
    sizer.Add(sash,1,wxEXPAND)
    sizer.Add(panel2,1,wxEXPAND)
    parent.SetSizer(sizer)
    parent.SetAutoLayout(true)
    return (panel1, panel2)

def makeSizer(obj):
    sizer = wxBoxSizer(wxVERTICAL)
    sizer.Add(obj,1,wxEXPAND)
    parent = obj.GetParent()
    parent.SetSizer(sizer)
    parent.SetAutoLayout(true)

def labelIt(obj,text):
    text = wxStaticText(obj,-1,text)
    panel = wxPanel(obj,-1)
    sizer = wxBoxSizer(wxVERTICAL)
    sizer.Add(text,0,wxALIGN_CENTER)
    sizer.Add(panel,1,wxEXPAND)
    obj.SetSizer(sizer)
    obj.SetAutoLayout(true)
    return panel

def makeButton(parent,sizer,text,obj,action):
    button = wxButton(parent, -1, text)
    sizer.Add(button,1,wxEXPAND)
    EVT_BUTTON(obj,button.GetId(),action)

import time,thread
def yieldThread():
    def yielder():
        global yieldThreadStop,threadLock
        threadLock.acquire()
        while yieldThreadStop==0:
            wxSafeYield()
            time.sleep(1)
        threadLock.release()
    global yieldThreadStop,threadLock
    yieldThreadStop = 0
    threadLock = thread.allocate_lock()
    thread.start_new_thread(yielder,())
def stopYieldThread():
    global yieldThreadStop,threadLock
    yieldThreadStop = 1
    threadLock.acquire()
    threadLock.release()

# ####################################################
# Code for manipulating 4DML with a wxTreeCtrl
# ####################################################
class FourSpaceTreeCtrl(wxTreeCtrl):
    def __init__(self,parent,id):
        wxTreeCtrl.__init__(self,parent,id)
        makeSizer(self)
    def setFourSpace(self,fourSpace):
        self.fourSpace = edit.FourSpaceEdit(fourSpace)
        # Construct the tree:
        self.DeleteAllItems()
        self.itemStack = []
        self.gotRoot = false
        self.reverseMap = {}
        self.walkFourSpace(fourSpace)
    def walkFourSpace(self,fourSpace):
        # called by setFourSpace
        for (p,subspace) in listsToPairs(fourSpace.calc_foreach(None)):
            name = p[0]
            # Take subspace; check if its ONLY element is ""
            # (cdata) (so can just append to this one)
            subspace.removeElement(p)
            # if no points in subspace, need all the data
            # anyway
            string = ""
            p2 = None
            if subspace.isEmpty():
                string=fourSpace.scopeOfElementAsString(p)
            elif name: # condition added emperically
                p2List,rList,_ = subspace.calc_foreach(None)
                if p2List: p2 = p2List[0]
                if len(p2List)==1 and p2[0] == "":
                    scope = subspace.scopeOfElement(p2)
                    toRemove = subspace.subSection(scopeDimension,scope)
                    subspace.removePoints(toRemove.getPoints())
                    for i in scope: string=string+i[0]
            if string:
                name = name + ": " + string
            else: name=name+(" (%d)" % p[positionDimension])
            # Now ready to start it
            self.start_element(name,p,p2)
            if not subspace.isEmpty():
                self.walkFourSpace(subspace)
            self.end_element()
    def start_element(self,name,mapping,mapping2):
        if (self.itemStack == []):
            assert self.gotRoot==false, \
                   "Tree has more than one root"
            newItem = self.AddRoot(name)
            self.gotRoot = true
        else:
            lastItem = self.itemStack[-1]
            newItem = self.AppendItem(lastItem,makePrintable(name))
        self.itemStack.append(newItem)
        self.SetPyData(newItem,mapping)
        self.reverseMap[mapping] = newItem
        if mapping2: self.reverseMap[mapping2] = newItem
        # (mapping2 added for case when first element is
        # cdata - e.g. promote some cdata (hence it appears
        # in 1st position) and it "merges" with the main
        # element (& still need to keep its mapping so we
        # can track the selection) - horrible hack **** not
        # sure if really want it like this) (alternative
        # might be to put cdata always as separate element,
        # including in the output for consistency; this
        # isn't concise)
    def end_element(self):
        lastItem = self.itemStack.pop()
        self.Expand(lastItem)
        # Colour again (see above)
        self.SetItemTextColour(lastItem,self.GetForegroundColour())
    def OnCompareItems(self,item1,item2):
        # Return (-, 0, +) if item1 (<, =, >) item2.
        # Do it by position in self.fourSpace
        # self.GetPyData(item) gives a point in the
        # element, from which the position can be read off.
        key1 = self.GetPyData(item1)[positionDimension]
        key2 = self.GetPyData(item2)[positionDimension]
        if key1 < key2: return -1
        elif key1 > key2: return 1
        else: return 0
    def moveUp(self):
        itemToMove = self.GetSelection()
        parent = self.GetItemParent(itemToMove)
        prev = self.GetPrevSibling(itemToMove)
        if itemToMove.IsOk() and parent.IsOk() and prev.IsOk():
            self.swapElements(itemToMove,prev)
            self.SortChildren(parent)
            return 1
        else: return 0
    def moveDown(self):
        itemToMove = self.GetSelection()
        parent = self.GetItemParent(itemToMove)
        next = self.GetNextSibling(itemToMove)
        if itemToMove.IsOk() and parent.IsOk() and next.IsOk():
            self.swapElements(itemToMove,next)
            self.SortChildren(parent)
            return 1
        else: return 0
    def moveLeft(self):
        itemToMove = self.GetSelection()
        oldParent = self.GetItemParent(itemToMove)
        newParent = self.GetItemParent(oldParent)
        if itemToMove.IsOk() and oldParent.IsOk() and newParent.IsOk():
            pos = self.GetPyData(oldParent)[positionDimension]+1
            newSel = self.fourSpace.moveElement( \
                self.GetPyData(itemToMove), \
                self.GetPyData(oldParent), \
                self.GetPyData(newParent), \
                pos)
            self.setFourSpace(self.fourSpace)
            # **** Don't like having to re-scan the whole lot
            self.selectElement(newSel)
            return 1
        else: return 0
    def moveRight(self):
        itemToMove = self.GetSelection()
        oldParent = self.GetItemParent(itemToMove)
        newParent = self.GetPrevSibling(itemToMove)
        if itemToMove.IsOk() and oldParent.IsOk() and newParent.IsOk():
            pos = 1 # **** Actually want to put it on the end, not the beginning
            newSel = self.fourSpace.moveElement( \
                self.GetPyData(itemToMove), \
                self.GetPyData(oldParent), \
                self.GetPyData(newParent), \
                pos)
            self.setFourSpace(self.fourSpace) # **** Don't like having to re-scan the whole lot
            self.selectElement(newSel)
            return 1
        else: return 0
    def delete(self):
        itemToDelete = self.GetSelection()
        parent = self.GetItemParent(itemToDelete)
        if itemToDelete.IsOk() and parent.IsOk():
            newSel = self.GetPyData(parent) # **** Really want next item, not parent
            self.fourSpace.deleteElement(self.GetPyData(itemToDelete),self.GetPyData(parent))
            self.setFourSpace(self.fourSpace) # **** Don't like having to re-scan the whole lot - can just remove from tree
            # self.selectElement(newSel)
            # **** Above doesn't work.  Perhaps because
            # delete mangles everything anyway (removes more
            # than it should; check epsilons)
            return 1
        else: return 0
    # **** Insert(/edit)
    # (use the "position holes" &c)
    def swapElements(self,item1,item2):
        elem1 = self.GetPyData(item1)
        elem2 = self.GetPyData(item2)
        (new_elem1,new_elem2) = self.fourSpace.swapElements(elem1,elem2)
        self.SetPyData(item1,new_elem1)
        self.SetPyData(item2,new_elem2)
        # and update self.reverseMap
        del self.reverseMap[elem1]
        del self.reverseMap[elem2]
        self.reverseMap[new_elem1] = item1
        self.reverseMap[new_elem2] = item2
    def selectElement(self,point):
        # Select (and make visible) whatever item has
        # 'point' (or an equivalent)
        assert self.reverseMap.has_key(point), \
               "Point %s not found in reverse map, which "\
               "only has the following points: %s" % \
               (point,self.reverseMap.keys())
        item = self.reverseMap[point]
        # We don't use introspection because it doesn't
        # always work (due to wxPython bugs)
        assert item, "Tree item for point %s not found" % (point,) # (need this otherwise get a segfault)
        self.SelectItem(item)
        self.EnsureVisible(item)
    def getChildList(self,item):
        list = []
        (item,cookie) = self.GetFirstChild(item,None)
        while item.IsOk():
            list.append(item)
            (item,cookie) = self.GetNextChild(item,cookie)
        return list

# ####################################################
# Code for a frame to view the input
# ####################################################
class InputFrame(wxFrame):
    def __init__(self, parent, ID, title, fourspace):
        wxFrame.__init__(self, parent, ID, title,
                         wxDefaultPosition, DefaultSize)
        tree = FourSpaceTreeCtrl(self,-1)
        self.Show(true)
        tree.setFourSpace(fourspace)

# ####################################################
# Code for the frame itself
# ####################################################
class MyFrame(wxFrame):
    def SetStatusText(self,text):
        # print text
        wxFrame.SetStatusText(self,text)
        wxSafeYield()
    def __init__(self, parent, ID, title, application,
                 input, model, debug):
        wxFrame.__init__(self, parent, ID, title,
                         wxDefaultPosition, DefaultSize)
        # could add a size to the above

        self.application = application # for sending idle
        # events etc (make sure updated)
        
        self.NextActionId = 100   # for creating the menus
        self.CreateStatusBar()

        self.showOutput = 1
        self.showLost = 0

        (leftPanel,rightPanel)=splitSash(self,wxHORIZONTAL)
        (wmodel,controls)=splitPanel(leftPanel,wxVERTICAL)
        (buttons,params)=splitPanel(controls,wxVERTICAL)
        (output,lost)=splitSash(rightPanel,wxVERTICAL)

        wmodel = labelIt(wmodel,"Model")
        self.modelTree = FourSpaceTreeCtrl(wmodel,-1)

        output = labelIt(output,"Output")
        self.outputTree = FourSpaceTreeCtrl(output,-1)
        makeSizer(self.outputTree)
        
        lost = labelIt(lost,"Lost Data")
        self.lostTree = FourSpaceTreeCtrl(lost,-1)
        makeSizer(self.lostTree)

        textCtrl = wxTextCtrl(params,-1,"") # "Parameters"
        makeSizer(textCtrl)
        textCtrl.SetBackgroundColour(textCtrl.GetParent().GetBackgroundColour())
        # because some versions of wxWindows always give it
        # a white background (resulting in some schemes
        # being unreadable)

        # box = wxBoxSizer(wxHORIZONTAL)
        box = wxGridSizer(2,3,3,3) # rows,cols,[vgap,hgap]

        # buttons, box, text, method
        makeButton(buttons,box,"Ins",self,self.NotImpl) # ****
        makeButton(buttons,box,"Up",self,self.MoveUp)
        makeButton(buttons,box,"Del",self,self.Delete)
        makeButton(buttons,box,"<-",self,self.MoveLeft)
        makeButton(buttons,box,"Dn",self,self.MoveDown)
        makeButton(buttons,box,"->",self,self.MoveRight)
        buttons.SetSizer(box)
        buttons.SetAutoLayout(true)

        menu = wxMenu()
        self.doMenuItem(menu,self.WriteOut,"Write &Output",
                        "Save the output to an XML file")
        self.doMenuItem(menu,self.OnAbout,"&About",
                        "Information about this program")
        menu.AppendSeparator()
        self.doMenuItem(menu,self.TimeToQuit,"E&xit",
                        "Terminate the program")
        menuBar = wxMenuBar()
        menuBar.Append(menu, "&File");

        menu = wxMenu()
        self.doMenuItem(menu,self.ShowIn,"&Input",
                        "Show the input as a tree")
        self.doMenuItem(menu,self.ShowText,"&Text only",
                        "Show output text without markup")
        menu.AppendSeparator()
        self.doMenuItem(menu,self.ToggleOut,"Toggle &Output","Toggles whether to show the output")
        self.doMenuItem(menu,self.ToggleLost,"Toggle &Lost Data","Toggles whether to show lost data")
        menuBar.Append(menu, "&View");

        menu = wxMenu()
        self.doMenuItem(menu,self.CallTree,"Capture call &tree",
                        "Capture and show the transform's call tree")
        menuBar.Append(menu, "&Debug");

        self.SetMenuBar(menuBar)

        self.Show(true)
        
        self.modelTree.setFourSpace(model)
        self.input=input
        if debug: self.CallTree(None)
        else: self.makeOutputTree()

    def OnAbout(self, event):
        dlg = wxMessageDialog(self,version.aboutMsg,
                              "About %s" % version.guiTitle, wxOK | wxICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
    def NotImpl(self, event):
        dlg = wxMessageDialog(self, "Not implemented yet.",
                              "Sorry",wxOK)
        dlg.ShowModal()
        dlg.Destroy()
    def doMenuItem(self,menu,action,text,status):
        menu.Append(self.NextActionId,text,status)
        EVT_MENU(self,self.NextActionId,action)
        self.NextActionId = self.NextActionId + 1
    def MoveUp(self,event):
        if self.modelTree.moveUp(): self.makeOutputTree()
    def MoveDown(self,event):
        if self.modelTree.moveDown(): self.makeOutputTree()
    def MoveLeft(self,event):
        if self.modelTree.moveLeft(): self.makeOutputTree()
    def MoveRight(self,event):
        if self.modelTree.moveRight(): self.makeOutputTree()
    def Delete(self,event):
        if self.modelTree.delete(): self.makeOutputTree()
    def TimeToQuit(self, event):
        self.Close(true)
    def ShowIn(self, event):
        InputFrame(self,-1,"View Input",self.input)
    def CallTree(self, event):
        class Tracer:
            def __init__(self):
                self.string = """<?xml version="1.0"?>"""
            def addString(self,s):
                self.string = self.string + s
        myTracer = Tracer()
        self.SetStatusText("Capturing transform call tree...")
        yieldThread()
        wasError = 0
        try:
            self.input.transformWrapper(self.modelTree.fourSpace,tracer=myTracer)
        except:
            wasError = 1
        stopYieldThread()
        self.SetStatusText("Ready")
        if wasError: self.show_error()
        else:
            # print makePrintable(myTracer.string) # **** do we want that?
            self.SetStatusText("Converting to tree control...")
            try:
                InputFrame(self,-1,"Call Tree",xmlStringToFourspace(makePrintable(myTracer.string)))
            except:
                self.show_error()
            self.SetStatusText("Ready")
    def show_error(self):
        dlg = wxMessageDialog(self,"%s" % (sys.exc_info()[1],),"Error",wxOK)
        dlg.ShowModal()
        dlg.Destroy()
    def ShowText(self, event):
        try:
            output = self.input.transformWrapper(self.modelTree.fourSpace,in_no_markup=1)
        except:
            self.show_error()
        dlg = wxMessageDialog(self,output,
                              "Text Only", wxOK)
        # **** Need a scrollable text box with wrap
        dlg.ShowModal()
        dlg.Destroy()
    def ToggleOut(self,event):
        self.showOutput = not self.showOutput
        self.makeOutputTree()
    def ToggleLost(self,event):
        dlg = wxMessageDialog(self, "Code to track lost data\nwas dropped from this version\nof the prototype\ndue to some algorithm re-writes\nthat made it awkward to maintain.",
                              "Sorry",wxOK)
        dlg.ShowModal()
        dlg.Destroy()
    def WriteOut(self, event):
        print makePrintable(self.outputData) # **** Must go to a file!
    def makeOutputTree(self):
        # **** Delete all items: Really want an incremental
        # update (or just sort the children of an existing
        # tree if only the order has changed), so that it's
        # quicker and selection/position/etc stay the same,
        # but OK for now.
        self.SetStatusText("Transforming...")
        yieldThread()
        self.outputTree.DeleteAllItems()
        self.lostTree.DeleteAllItems()
        if self.showOutput:
            wasError = 0
            try:
                output = xmlStringToFourspace(self.input.transformWrapper(self.modelTree.fourSpace,alwaysOutputXML=1))
                # print self.input.transformWrapper(self.modelTree.fourSpace,alwaysOutputXML=1)
            except:
                wasError = 1
            stopYieldThread()
            if wasError:
                self.show_error()
                self.outputTree.setFourSpace(notShown)
                self.lostTree.setFourSpace(notShown)
                self.SetStatusText("There was an error")
                return
            self.SetStatusText("Converting to tree control...")
            yieldThread()
            self.outputTree.setFourSpace(output)
            self.outputData = output.convertToXML() # (save it in case the user wants to write it out)
            # (this did say convertToXML and then use
            # xmlToTree, but that's deprecated)
            stopYieldThread()
            self.SetStatusText("Getting lost data...")
            yieldThread()
            if self.showLost:
                assert 0,"should never get here in this version of the prototype"
                # lost = self.input.getLostData(output)
                self.lostTree.setFourSpace(lost)
            else:
                self.lostTree.setFourSpace(notShown)
        else:
            self.outputTree.setFourSpace(notShown)
            self.lostTree.setFourSpace(notShown)
        stopYieldThread()
        self.SetStatusText("Ready")

class MyApp(wxApp):
    def OnInit(self):
        global GInput, GModel, GDebug
        frame=MyFrame(NULL, -1, version.guiTitle,
                      self, GInput, GModel, GDebug)
        self.SetTopWindow(frame)
        return true

def doGUI(input, model, debug=0):
    global GInput, GModel, GDebug
    GInput = input
    GModel = model
    GDebug = debug
    app = MyApp(0)
    app.MainLoop()
