using MVRuntimeLib;
using MVRuntimeLib.Extensions;

using Microsoft.Scripting.Runtime;

[assembly: ExtensionType(typeof(IMVHighlight), typeof(IMVHighlightExtension))]

namespace MVRuntimeLib.Extensions
{
    using System;
    using System.Collections.Generic;
    using System.Diagnostics;
    using System.IO;

// ReSharper disable InconsistentNaming
    public static class IMVHighlightExtension
// ReSharper restore InconsistentNaming
    {
        public static Tuple<double, double> Get(this IMVHighlight self, int index)
        {
            double start, end;
            self.GetHighlight((uint)index, out start, out end);
            return new Tuple<double, double>(start, end);
        }

        public static List<Tuple<double, double>> Highlights(this IMVHighlight self)
        {
            var highlights = new List<Tuple<double, double>>();
            for (int i = 0; i < self.HighlightCount; i++)
            {
                highlights.Add(self.Get(i));
            }

            return highlights;
        }

        public static void VerifyUserDescriptors(this IMVHighlight self)
        {
            var highlights = self.Highlights();
            var temp = Path.Combine(Path.GetTempPath(), "temp.mpd");
            try
            {
                self.SaveHighlightsToFile(temp, 0);
                self.ClearAllHighlights();
                Debug.Assert(self.HighlightCount == 0, "ClearAllHighlights failed");

                self.LoadHighlightsFromFile(temp, 0);
            }
            finally
            {
                if (File.Exists(temp))
                {
                    File.Delete(temp);
                }
            }

            Debug.Assert(self.HighlightCount == highlights.Count);
            for (int i = 0; i < highlights.Count; i++)
            {
                var tuple = self.Get(i);
                Debug.Assert(tuple.Equals(highlights[i]));
            }
        }
    }
}

