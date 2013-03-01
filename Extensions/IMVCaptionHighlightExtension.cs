using Microsoft.Scripting.Runtime;
using MVRuntimeLib;
using MVRuntimeLib.Extensions;

[assembly: ExtensionType(typeof(IMVCaptionHighlight), typeof(IMVCaptionHighlightExtension))]

namespace MVRuntimeLib.Extensions
{
    using System;
    using System.Collections.Generic;
    using System.Diagnostics;
    using System.IO;

// ReSharper disable InconsistentNaming
    public static class IMVCaptionHighlightExtension
// ReSharper restore InconsistentNaming
    {
        public static Tuple<string, double, double, IMVTextFormat> Get(this IMVCaptionHighlight self, int index)
        {
            string caption;
            double start, end;
            IMVTextFormat format;
            self.GetCaptionHighlight((uint)index, out caption, out start, out end, out format);
            return new Tuple<string, double, double, IMVTextFormat>(caption, start, end, format);
        }

        /// <summary>
        /// Returns a list of all created highlights
        /// </summary>
        /// <param name="self">The IMVCaptionHighlight instance</param>
        /// <returns>List of highlight tuples</returns>
        public static List<Tuple<string, double, double, IMVTextFormat>> Highlights(this IMVCaptionHighlight self)
        {
            
            var highlights = new List<Tuple<string, double, double, IMVTextFormat>>();
            for (int i = 0; i < self.CaptionHighlightCount; i++)
            {
                highlights.Add(self.Get(i));
            }

            return highlights;
        }

        /// <summary>
        /// Returns a list of all created highlights
        /// </summary>
        /// <param name="self">The IMVCaptionHighlight instance</param>
        /// <returns>List of highlight tuples</returns>
        public static void VerifyUserDescriptors(this IMVCaptionHighlight self)
        {
            var highlights = self.Highlights();
            var temp = Path.Combine(Path.GetTempPath(), "temp.mpd");
            try
            {
                self.SaveCaptionsToFile(temp, 0);
                self.ClearAllCaptionHighlights();
                Debug.Assert(self.CaptionHighlightCount == 0, "ClearAllHighlights failed");

                self.LoadCaptionsFromFile(temp, 0);
            }
            finally
            {
                if (File.Exists(temp))
                {
                    File.Delete(temp);
                }
            }

            Debug.Assert(self.CaptionHighlightCount == highlights.Count);
            Func<double, double, bool> equals = (x, y) =>
                {
                    // compensate for floating point differences
                    var difference = Math.Abs(x * 0.00001);
                    return Math.Abs(x - y) <= difference;
                };

            for (int i = 0; i < highlights.Count; i++)
            {
                var tuple1 = self.Get(i);
                var tuple2 = highlights[i];
                Debug.Assert(
                    tuple1.Item1 == tuple2.Item1 && equals(tuple1.Item2, tuple2.Item2)
                    && equals(tuple1.Item3, tuple2.Item3));
            }
        }
    }
}

