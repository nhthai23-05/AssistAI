import { Moon, Sun, Bell, Lock, Globe, Palette } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { Separator } from './ui/separator';

interface SettingsInterfaceProps {
  darkMode: boolean;
  onDarkModeToggle: () => void;
}

export function SettingsInterface({ darkMode, onDarkModeToggle }: SettingsInterfaceProps) {
  return (
    <div className="flex-1 flex flex-col h-full">
      <div className={`px-6 py-4 border-b ${
        darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'
      }`}>
        <h2 className={darkMode ? 'text-white' : 'text-gray-900'}>Settings</h2>
        <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
          Manage your preferences and account settings
        </p>
      </div>

      <div className={`flex-1 overflow-auto ${darkMode ? 'bg-gray-950' : 'bg-gray-50'}`}>
        <div className="p-6 max-w-3xl space-y-6">
          <Card className={darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="w-5 h-5" />
                <span className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                  Appearance
                </span>
              </CardTitle>
              <CardDescription className={darkMode ? 'text-gray-500' : 'text-gray-600'}>
                Customize how the dashboard looks
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                    Dark Mode
                  </Label>
                  <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-600'}`}>
                    Use dark theme across the dashboard
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Sun className="w-4 h-4 text-gray-400" />
                  <Switch checked={darkMode} onCheckedChange={onDarkModeToggle} />
                  <Moon className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className={darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5" />
                <span className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                  Notifications
                </span>
              </CardTitle>
              <CardDescription className={darkMode ? 'text-gray-500' : 'text-gray-600'}>
                Control how you receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                    Email Notifications
                  </Label>
                  <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-600'}`}>
                    Receive updates via email
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
              <Separator className={darkMode ? 'bg-gray-800' : 'bg-gray-200'} />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                    Calendar Reminders
                  </Label>
                  <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-600'}`}>
                    Get reminders for upcoming events
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
              <Separator className={darkMode ? 'bg-gray-800' : 'bg-gray-200'} />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                    Assistant Suggestions
                  </Label>
                  <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-600'}`}>
                    Show proactive AI suggestions
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>

          <Card className={darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lock className="w-5 h-5" />
                <span className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                  Privacy & Security
                </span>
              </CardTitle>
              <CardDescription className={darkMode ? 'text-gray-500' : 'text-gray-600'}>
                Manage your data and security preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                    Two-Factor Authentication
                  </Label>
                  <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-600'}`}>
                    Add an extra layer of security
                  </p>
                </div>
                <Switch />
              </div>
              <Separator className={darkMode ? 'bg-gray-800' : 'bg-gray-200'} />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                    Activity Logging
                  </Label>
                  <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-600'}`}>
                    Save logs of assistant interactions
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>

          <Card className={darkMode ? 'bg-gray-900 border-gray-800' : 'bg-white border-gray-200'}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5" />
                <span className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                  Language & Region
                </span>
              </CardTitle>
              <CardDescription className={darkMode ? 'text-gray-500' : 'text-gray-600'}>
                Set your language and timezone preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                  Language
                </Label>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  English (US)
                </p>
              </div>
              <Separator className={darkMode ? 'bg-gray-800' : 'bg-gray-200'} />
              <div className="space-y-2">
                <Label className={darkMode ? 'text-gray-200' : 'text-gray-900'}>
                  Timezone
                </Label>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Pacific Standard Time (PST)
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
