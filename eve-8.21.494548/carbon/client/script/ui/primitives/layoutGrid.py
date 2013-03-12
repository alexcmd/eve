#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/primitives/layoutGrid.py
import uicls
import uiconst
import uiutil
import blue
import telemetry
COLUMN_WIDTH_AUTOFIT = -1
COLUMN_WIDTH_FILL = -2
uiconst.COLUMN_WIDTH_AUTOFIT = COLUMN_WIDTH_AUTOFIT
uiconst.COLUMN_WIDTH_FILL = COLUMN_WIDTH_FILL
TOPBOTTOM_ALIGNMENTS = (uiconst.TOTOP,
 uiconst.TOBOTTOM,
 uiconst.TOTOP_NOPUSH,
 uiconst.TOBOTTOM_NOPUSH,
 uiconst.TOTOP_PROP,
 uiconst.TOBOTTOM_PROP)
LEFTRIGHT_ALIGNMENTS = (uiconst.TOLEFT,
 uiconst.TORIGHT,
 uiconst.TOLEFT_NOPUSH,
 uiconst.TORIGHT_NOPUSH,
 uiconst.TOLEFT_PROP,
 uiconst.TORIGHT_PROP)
CENTER_ALIGNMENTS = (uiconst.CENTER,
 uiconst.CENTERBOTTOM,
 uiconst.CENTERTOP,
 uiconst.CENTERLEFT,
 uiconst.CENTERRIGHT)

class LayoutGridCell(uicls.Container):
    __guid__ = 'uicls.LayoutGridCell'
    _content = None

    def ApplyAttributes(self, attributes):
        attributes.state = uiconst.UI_PICKCHILDREN
        attributes.clipChildren = True
        uicls.Container.ApplyAttributes(self, attributes)
        cellPadding = attributes.cellPadding
        if isinstance(cellPadding, tuple):
            self.cellPadding = cellPadding
        elif isinstance(cellPadding, int):
            self.cellPadding = (cellPadding,
             cellPadding,
             cellPadding,
             cellPadding)
        else:
            self.cellPadding = (0, 0, 0, 0)
        self._content = uicls.Container(parent=self, padding=self.cellPadding)
        cellObject = attributes.cellObject
        if cellObject:
            if cellObject.align != uiconst.TOALL:
                cellObject.UpdateAlignment = lambda *args: self.UpdateCellObjectAlignment(cellObject, *args)
            self._content.children.append(cellObject)
        self.colSpan = attributes.colSpan or 1
        self.rowSpan = attributes.rowSpan or 1

    def UpdateCellObjectAlignment(self, cellObject, *args):
        preX = cellObject.renderObject.displayX
        preY = cellObject.renderObject.displayY
        preWidth = cellObject.renderObject.displayWidth
        preHeight = cellObject.renderObject.displayHeight
        ret = uicls.Base.UpdateAlignment(cellObject, *args)
        align = cellObject.align
        if align in TOPBOTTOM_ALIGNMENTS:
            if preHeight != cellObject.renderObject.displayHeight or preY != cellObject.renderObject.displayY:
                self.parent.FlagCellSizesDirty()
        elif align in LEFTRIGHT_ALIGNMENTS:
            if preWidth != cellObject.renderObject.displayWidth or preX != cellObject.renderObject.displayX:
                self.parent.FlagCellSizesDirty()
        elif preX != cellObject.renderObject.displayX:
            self.parent.FlagCellSizesDirty()
        elif preY != cellObject.renderObject.displayY:
            self.parent.FlagCellSizesDirty()
        elif preWidth != cellObject.renderObject.displayWidth:
            self.parent.FlagCellSizesDirty()
        elif preHeight != cellObject.renderObject.displayHeight:
            self.parent.FlagCellSizesDirty()
        return ret

    def Close(self, *args):
        parent = self.parent
        uicls.Container.Close(self, *args)
        if parent and not parent.destroyed:
            parent.FlagGridLayoutDirty()

    def GetContentSize(self, columnIndex, setColumnWidths):
        if self._content.children:
            cellObject = self._content.children[0]
            cellObjectAlign = cellObject.align
            if cellObjectAlign in CENTER_ALIGNMENTS:
                neededCellWidth = cellObject.displayWidth + uicore.ScaleDpiF(cellObject.padLeft + cellObject.padRight + cellObject.left * 2)
                neededCellHeight = cellObject.displayHeight + uicore.ScaleDpiF(cellObject.padTop + cellObject.padBottom + cellObject.top * 2)
            elif cellObjectAlign not in uiconst.AFFECTEDBYPUSHALIGNMENTS:
                neededCellWidth = cellObject.displayWidth + uicore.ScaleDpiF(cellObject.padLeft + cellObject.padRight + cellObject.left)
                neededCellHeight = cellObject.displayHeight + uicore.ScaleDpiF(cellObject.padTop + cellObject.padBottom + cellObject.top)
            elif cellObjectAlign in TOPBOTTOM_ALIGNMENTS:
                neededCellWidth = 0
                neededCellHeight = cellObject.displayHeight + uicore.ScaleDpiF(cellObject.padTop + cellObject.padBottom + cellObject.top)
            elif cellObjectAlign in LEFTRIGHT_ALIGNMENTS:
                neededCellWidth = cellObject.displayWidth + uicore.ScaleDpiF(cellObject.padLeft + cellObject.padRight + cellObject.left)
                neededCellHeight = 0
            elif cellObject.align == uiconst.TOALL:
                neededCellWidth = uicore.ScaleDpiF(32)
                neededCellHeight = uicore.ScaleDpiF(32)
            else:
                neededCellWidth = max(1, cellObject.displayWidth + uicore.ScaleDpiF(cellObject.padLeft + cellObject.padRight))
                neededCellHeight = max(1, cellObject.displayHeight + uicore.ScaleDpiF(cellObject.padTop + cellObject.padBottom))
            ccpl, ccpt, ccpr, ccpb = self.cellPadding
            columnWidth = setColumnWidths.get(columnIndex, COLUMN_WIDTH_AUTOFIT)
            if columnWidth in (COLUMN_WIDTH_FILL, COLUMN_WIDTH_AUTOFIT):
                return (max(1, neededCellWidth + uicore.ScaleDpiF(self.padLeft + self.padRight + ccpl + ccpr)), max(1, neededCellHeight + uicore.ScaleDpiF(self.padTop + self.padBottom + ccpt + ccpb)))
            if isinstance(columnWidth, int):
                return (max(1, uicore.ScaleDpiF(self.padLeft + columnWidth + self.padRight + ccpl + ccpr)), max(1, neededCellHeight + uicore.ScaleDpiF(self.padTop + self.padBottom + ccpt + ccpb)))
        return (max(1, uicore.ScaleDpiF(self.padLeft + self.padRight)), max(1, uicore.ScaleDpiF(self.padTop + self.padBottom)))

    def UpdateAlignmentAsRoot(self, *args):
        if not getattr(self, '_content', None):
            return
        budget = (0,
         0,
         self.displayWidth,
         self.displayHeight)
        self._content._alignmentDirty = True
        self._content.Traverse(budget)


class LayoutGrid(uicls.Container):
    __guid__ = 'uicls.LayoutGrid'
    default_align = uiconst.CENTER
    default_columns = 2
    default_cellPadding = 0
    default_cellSpacing = 6
    default_cellBgColor = None
    _sizesDirty = False
    _layoutDirty = False
    _fixedGridWidth = None
    _columns = 2

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        cellPadding = attributes.cellPadding
        if isinstance(cellPadding, tuple):
            self._grid_cellPadding = cellPadding
        elif isinstance(cellPadding, int):
            self._grid_cellPadding = (cellPadding,
             cellPadding,
             cellPadding,
             cellPadding)
        else:
            self._grid_cellPadding = None
        cellSpacing = attributes.get('cellSpacing', self.default_cellSpacing)
        if isinstance(cellSpacing, int):
            self._grid_cellSpacing = (cellSpacing, cellSpacing)
        elif isinstance(cellSpacing, tuple) and len(cellSpacing) == 2:
            self._grid_cellSpacing = cellSpacing
        else:
            self._grid_cellSpacing = (0, 0)
        self._grid_cellBgColor = attributes.get('cellBgColor', None)
        self._columns = attributes.get('columns', self.default_columns)
        self._layoutData = []
        self._setColumnWidths = {}
        self._fixedGridWidth = None
        self.children.insert = self._InsertChild
        self.children.append = self._AppendChild
        self.children.remove = self._RemoveChild

    def _InsertChild(self, idx, obj):
        if not isinstance(obj, uicls.LayoutGridCell):
            return self.AddCell(cellObject=obj, idx=idx)
        return uicls.UIChildrenList.insert(self.children, idx, obj)

    def _AppendChild(self, obj):
        self._InsertChild(-1, obj)

    def _RemoveChild(self, obj):
        if isinstance(obj, uicls.LayoutGridCell):
            return uicls.UIChildrenList.remove(self.children, obj)
        return uicls.UIChildrenList.remove(self.children, obj.parent)

    def _OnSizeChange_NoBlock(self, *args):
        uicls.Container._OnSizeChange_NoBlock(self, *args)
        self._sizesDirty = True

    def FlagCellSizesDirty(self):
        self._sizesDirty = True
        self.FlagAlignmentDirty()

    def FlagGridLayoutDirty(self):
        self._layoutDirty = True
        self.FlagAlignmentDirty()

    def AddCell(self, cellObject = None, colSpan = 1, rowSpan = 1, cellPadding = None, bgColor = None, bgTexturePath = None, **kwds):
        cell = uicls.LayoutGridCell(parent=self, align=uiconst.NOALIGN, colSpan=colSpan, rowSpan=rowSpan, cellObject=cellObject, cellPadding=(cellPadding or self._grid_cellPadding), bgColor=(bgColor or self._grid_cellBgColor), bgTexturePath=bgTexturePath, **kwds)
        self.FlagGridLayoutDirty()

    def CloseCellByIndex(self, cellIndex):
        if len(self.children) > cellIndex:
            self.children[cellIndex].Close()
            self.FlagGridLayoutDirty()

    def Flush(self):
        uicls.Container.Flush(self)
        self.FlagGridLayoutDirty()

    def SetFixedGridWidth(self, fixedWidth = None):
        if fixedWidth and self.align in TOPBOTTOM_ALIGNMENTS:
            raise RuntimeError('Cannot set fixedWidth when using TOTOP or TOBOTTOM alignment')
        elif self.align in uiconst.AFFECTEDBYPUSHALIGNMENTS:
            raise RuntimeError('Cannot set fixed grid size when alignment is', self.alignment)
        self._fixedGridWidth = fixedWidth
        self.FlagCellSizesDirty()

    def SetColumnWidth(self, columnIndex, columnWidth):
        self._setColumnWidths[columnIndex] = columnWidth
        self.FlagCellSizesDirty()

    @telemetry.ZONE_FUNCTION
    def Traverse(self, mbudget):
        if self.destroyed:
            return mbudget
        if self._alignmentDirty:
            cBudget = self.UpdateAlignment(mbudget)
        elif self.display:
            cBudget = self.ConsumeBudget(mbudget)
        if self._layoutDirty:
            self.UpdateGridLayout()
        if self._sizesDirty:
            self.UpdateCellsPositionAndSize()
        return cBudget

    def UpdateCellsPositionAndSize(self):
        fixedColumns = {}
        spreadColumns = []
        for columnIndex, columnWidthValue in self._setColumnWidths.iteritems():
            if columnWidthValue == COLUMN_WIDTH_AUTOFIT:
                continue
            elif columnWidthValue == COLUMN_WIDTH_FILL:
                spreadColumns.append(columnIndex)
            elif isinstance(columnWidthValue, int):
                fixedColumns[columnIndex] = columnWidthValue

        rows = self._layoutData
        rowHeights = {}
        spreadRows = []
        columnWidths = {}
        for rowIndex, columnData in enumerate(rows):
            for columnIndex, cell in enumerate(columnData):
                if cell is None or cell == '__taken__' or cell == '__taken__fromabove__':
                    continue
                cW, cH = cell.GetContentSize(columnIndex, self._setColumnWidths)
                if cell.rowSpan == 1:
                    rowHeights.setdefault(rowIndex, []).append(cH)
                else:
                    spreadRows.append((rowIndex, cell.rowSpan, cH))
                if columnIndex in fixedColumns:
                    columnWidths[columnIndex] = [uicore.ScaleDpiF(fixedColumns[columnIndex])]
                else:
                    colSpan = cell.colSpan
                    if columnIndex + colSpan > self._columns:
                        colSpan = min(self._columns - columnIndex, colSpan)
                    splitWidth = cW / colSpan
                    for i in xrange(colSpan):
                        columnWidths.setdefault(columnIndex + i, []).append(splitWidth)

        for rowIndex, rowSpan, spanHeight in spreadRows:
            totalHeight = 0
            for i in xrange(rowSpan):
                if rowIndex + i in rowHeights:
                    totalHeight += max(rowHeights[rowIndex + i])
                else:
                    rowHeights[rowIndex + i] = [0]

            toSpread = max(0, spanHeight - totalHeight)
            if toSpread:
                used = 0
                for rowIndexSpan in xrange(rowSpan):
                    maxRowHeight = max(rowHeights.get(rowIndex + rowIndexSpan, [0]))
                    if rowIndexSpan == rowSpan - 1:
                        rowHeights[rowIndex + rowIndexSpan] = [maxRowHeight + (toSpread - used)]
                        continue
                    addSpread = toSpread / rowSpan
                    rowHeights[rowIndex + rowIndexSpan] = [maxRowHeight + addSpread]
                    used += addSpread

        scaledCellSpacingX = int(round(uicore.ScaleDpiF(self._grid_cellSpacing[0])))
        scaledCellSpacingY = int(round(uicore.ScaleDpiF(self._grid_cellSpacing[1])))
        if spreadColumns:
            fillWidth = None
            if self._fixedGridWidth:
                fillWidth = uicore.ScaleDpiF(self._fixedGridWidth)
            elif self.align in uiconst.AFFECTEDBYPUSHALIGNMENTS:
                fillWidth = self.displayWidth
            if fillWidth:
                totalColumnWidths = sum([ max(v) for k, v in columnWidths.items() if k not in spreadColumns ])
                totalColumnWidths += scaledCellSpacingX * (len(columnWidths) + 1)
                toSpread = max(0, fillWidth - totalColumnWidths)
                if toSpread:
                    used = 0
                    splitWidth = toSpread / len(spreadColumns)
                    for columnIndex in spreadColumns:
                        if columnIndex == spreadColumns[-1]:
                            columnWidths[columnIndex] = [toSpread - used]
                            continue
                        columnWidths[columnIndex] = [splitWidth]
                        used += splitWidth

                else:
                    for columnIndex in spreadColumns:
                        columnWidths[columnIndex] = [0]

        colsMaxed = [ (k, max(v)) for k, v in columnWidths.items() ]
        colsMaxed.sort()
        rowsMaxed = [ (k, max(v)) for k, v in rowHeights.items() ]
        rowsMaxed.sort()
        maxScaledHeight = 0
        maxScaledWidth = 0
        for rowIndex, columnData in enumerate(rows):
            for columnIndex, cell in enumerate(columnData):
                if cell is None or cell == '__taken__' or cell == '__taken__fromabove__':
                    continue
                rowSpan = cell.rowSpan
                colSpan = cell.colSpan
                if columnIndex + colSpan > self._columns:
                    colSpan = min(self._columns - columnIndex, colSpan)
                cellWidth = sum([ colsMaxed[columnIndex + i][1] for i in xrange(colSpan) ]) + scaledCellSpacingX * (colSpan - 1)
                cellHeight = sum([ rowsMaxed[rowIndex + i][1] for i in xrange(rowSpan) ]) + scaledCellSpacingY * (rowSpan - 1)
                cellLeft = sum([ w[1] for w in colsMaxed[:columnIndex] ]) + scaledCellSpacingX * (columnIndex + 1)
                cellTop = sum([ h[1] for h in rowsMaxed[:rowIndex] ]) + scaledCellSpacingY * (rowIndex + 1)
                maxScaledWidth = max(maxScaledWidth, cellLeft + cellWidth + scaledCellSpacingX)
                maxScaledHeight = max(maxScaledHeight, cellTop + cellHeight + scaledCellSpacingY)
                preCellLeft, preCellTop, preCellWidth, preCellHeight = cell.displayRect
                cell.displayRect = (cellLeft,
                 cellTop,
                 cellWidth,
                 cellHeight)
                if preCellWidth != cellWidth or preCellHeight != cellHeight:
                    uicore.uilib.alignIslands.append(cell)

        if self.align in TOPBOTTOM_ALIGNMENTS:
            self.width = 0
            self.height = uicore.ReverseScaleDpi(maxScaledHeight)
        elif self.align in LEFTRIGHT_ALIGNMENTS:
            self.width = self._fixedGridWidth or uicore.ReverseScaleDpi(maxScaledWidth)
            self.height = 0
        elif self.align not in uiconst.AFFECTEDBYPUSHALIGNMENTS:
            self.width = self._fixedGridWidth or uicore.ReverseScaleDpi(maxScaledWidth)
            self.height = uicore.ReverseScaleDpi(maxScaledHeight)
        self._sizesDirty = False

    def UpdateGridLayout(self):
        rows = []
        rowIndex = 0
        columnIndex = 0
        taken = []
        for cell in self.children:
            rowSpan = cell.rowSpan
            colSpan = cell.colSpan
            if (rowIndex, columnIndex) in taken:
                rowIndex, columnIndex = self.GetFirstEmpty(rows)
            if columnIndex + colSpan > self._columns:
                colSpan = min(self._columns - columnIndex, colSpan)
            for columnIndexShift in xrange(colSpan):
                for rowIndexShift in xrange(rowSpan):
                    while len(rows) <= rowIndex + rowIndexShift:
                        rows.append([None] * self._columns)

                    if rows[rowIndex + rowIndexShift][columnIndex + columnIndexShift]:
                        cell.colSpan = columnIndexShift
                        continue
                    if not columnIndexShift:
                        if not rowIndexShift:
                            register = cell
                        else:
                            register = '__taken__fromabove__'
                    else:
                        register = '__taken__'
                    taken.append((rowIndex + rowIndexShift, columnIndex + columnIndexShift))
                    rows[rowIndex + rowIndexShift][columnIndex + columnIndexShift] = register

            columnIndex = min(self._columns, columnIndex + colSpan)
            if columnIndex == self._columns:
                columnIndex = 0
                rowIndex += 1

        self._layoutData = rows
        self._layoutDirty = False
        self._sizesDirty = True

    def GetFirstEmpty(self, rows):
        rowIndex = 0
        for rowData in rows:
            for columnIndex, cell in enumerate(rowData):
                if cell is None:
                    return (rowIndex, columnIndex)

            rowIndex += 1

        rows.append([None] * self._columns)
        return (rowIndex, 0)

    @classmethod
    def Test(cls):
        uicls.Window.CloseIfOpen(windowID='LayoutGrid')
        wnd = uicls.Window.Open(windowID='LayoutGrid')
        wnd.SetTopparentHeight(0)
        main = wnd.GetMainArea()
        wnd._scrollContainer = uicls.ScrollContainer(parent=main, padding=4)
        wnd._scrollContainer.verticalScrollBar.align = uiconst.TORIGHT_NOPUSH
        wnd._scrollContainer.horizontalScrollBar.align = uiconst.TOBOTTOM_NOPUSH
        grid = uicls.LayoutGrid(parent=wnd._scrollContainer, align=uiconst.TOTOP, name='LayoutGrid', state=uiconst.UI_NORMAL, columns=5, cellPadding=12, cellSpacing=16, cellBgColor=(1, 1, 1, 0.1))
        lorem = u'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque rutrum neque ut metus pharetra malesuada. Vivamus mollis vulputate ornare. Quisque condimentum interdum arcu, nec pellentesque tellus venenatis non. Fusce nec feugiat libero. Nulla non velit felis. Morbi accumsan interdum erat sodales egestas. In mauris lorem, cursus et posuere sit amet, aliquet sit amet turpis. Maecenas tincidunt fringilla congue. Maecenas eu nibh quis mauris placerat vulputate. Curabitur condimentum arcu ut dui aliquet quis blandit ligula consectetur. Morbi consectetur egestas tortor, ut interdum nibh viverra id. Proin mattis eleifend dignissim. In eget laoreet nisl. '
        grid.SetColumnWidth(1, COLUMN_WIDTH_FILL)
        grid.SetColumnWidth(2, COLUMN_WIDTH_FILL)
        grid.AddCell(cellObject=uicls.Button(label='Bless', align=uiconst.CENTER), rowSpan=2)
        t = uicls.EveLabelMedium(text=lorem, align=uiconst.TOTOP)
        grid.AddCell(cellObject=t, colSpan=3, rowSpan=3)
        grid.AddCell()
        uicls.Button(label='Hallo', parent=grid)
        uicls.SinglelineEdit(align=uiconst.TOPLEFT, parent=grid)
        grid.AddCell()
        grid.AddCell(bgColor=(1, 0, 0, 0.25))
        uicls.Button(label='Bless', align=uiconst.CENTER, parent=grid)
        t = uicls.EveLabelMedium(text='Quisque rutrum neque ut metus pharetra malesuada', align=uiconst.TOTOP)
        grid.AddCell(cellObject=t, bgColor=(0, 0, 1, 0.25))
        grid.AddCell()
        uicls.EveLabelMedium(text='Vivamus mollis vulputate ornare', align=uiconst.TOTOP, parent=grid)
        return grid