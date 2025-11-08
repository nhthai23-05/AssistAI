import { FileSpreadsheet, MoreVertical } from 'lucide-react';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from './ui/dropdown-menu';

interface SheetFile {
  id: string;
  name: string;
  lastModified: string;
  owner: string;
}

interface SheetsInterfaceProps {
  darkMode: boolean;
}

export function SheetsInterface({ darkMode }: SheetsInterfaceProps) {
  const sheets: SheetFile[] = [
    {
      id: '1',
      name: 'Q4 Budget Planning',
      lastModified: 'November 7, 2025',
      owner: 'You',
    },
    {
      id: '2',
      name: 'Project Timeline',
      lastModified: 'November 6, 2025',
      owner: 'Sarah Chen',
    },
    {
      id: '3',
      name: 'Team Performance Metrics',
      lastModified: 'November 5, 2025',
      owner: 'You',
    },
    {
      id: '4',
      name: 'Client Database',
      lastModified: 'November 3, 2025',
      owner: 'Mike Johnson',
    },
    {
      id: '5',
      name: 'Marketing Campaign Data',
      lastModified: 'October 30, 2025',
      owner: 'Emma Williams',
    },
    {
      id: '6',
      name: 'Inventory Tracking',
      lastModified: 'October 28, 2025',
      owner: 'You',
    },
  ];

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className={`px-6 py-4 border-b ${
        darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'
      }`}>
        <h2 className={darkMode ? 'text-white' : 'text-gray-900'}>Google Sheets</h2>
        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          Your connected spreadsheets
        </p>
      </div>

      <div className={`flex-1 overflow-auto ${darkMode ? 'bg-gray-950' : 'bg-gray-50'}`}>
        <div className="p-6">
          <div className={`rounded-lg border ${
            darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'
          }`}>
            <Table>
              <TableHeader>
                <TableRow className={darkMode ? 'border-gray-800 hover:bg-gray-800' : 'border-gray-200'}>
                  <TableHead className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                    File Name
                  </TableHead>
                  <TableHead className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                    Last Modified
                  </TableHead>
                  <TableHead className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                    Owner
                  </TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sheets.map((sheet) => (
                  <TableRow
                    key={sheet.id}
                    className={`cursor-pointer ${
                      darkMode
                        ? 'border-gray-800 hover:bg-gray-800'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded ${
                          darkMode ? 'bg-green-900/30' : 'bg-green-50'
                        }`}>
                          <FileSpreadsheet className={`w-5 h-5 ${
                            darkMode ? 'text-green-400' : 'text-green-600'
                          }`} />
                        </div>
                        <span className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                          {sheet.name}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                      {sheet.lastModified}
                    </TableCell>
                    <TableCell className={darkMode ? 'text-gray-400' : 'text-gray-600'}>
                      {sheet.owner}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className={darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}
                          >
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>Open</DropdownMenuItem>
                          <DropdownMenuItem>Share</DropdownMenuItem>
                          <DropdownMenuItem>Rename</DropdownMenuItem>
                          <DropdownMenuItem className="text-red-600">Remove</DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  );
}
