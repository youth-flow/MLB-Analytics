using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;

internal static class Program
{
    private static string Quote(string value)
    {
        return "\"" + value.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
    }

    public static int Main(string[] args)
    {
        string baseDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        string script = Path.Combine(baseDirectory, "soffice-word-shim.ps1");
        var command = new StringBuilder();
        command.Append("-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ");
        command.Append(Quote(script));
        foreach (string arg in args)
        {
            command.Append(' ');
            command.Append(Quote(arg));
        }

        var startInfo = new ProcessStartInfo
        {
            FileName = "powershell.exe",
            Arguments = command.ToString(),
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };
        using (Process process = Process.Start(startInfo))
        {
            string stdout = process.StandardOutput.ReadToEnd();
            string stderr = process.StandardError.ReadToEnd();
            process.WaitForExit();
            Console.Out.Write(stdout);
            Console.Error.Write(stderr);
            return process.ExitCode;
        }
    }
}

