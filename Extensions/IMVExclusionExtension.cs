using Microsoft.Scripting.Runtime;
using MVRuntimeLib;
using MVRuntimeLib.Extensions;

[assembly: ExtensionType(typeof(IMVExclude), typeof(IMVExclusionExtension))]

namespace MVRuntimeLib.Extensions
{
    using System;
    using System.Collections.Generic;
    using System.Diagnostics;
    using System.IO;

// ReSharper disable InconsistentNaming
    public static class IMVExclusionExtension
// ReSharper restore InconsistentNaming
    {
        public static Tuple<double, double> Get(this IMVExclude self, int index)
        {
            double start, end;
            self.GetExclusion((uint)index, out start, out end);
            return new Tuple<double, double>(start, end);
        }

        /// <summary>
        /// Returns a list of all created exclusions
        /// </summary>
        /// <param name="self">The IMVExclusion instance</param>
        /// <returns>List of exclusion tuples</returns>
        public static List<Tuple<double, double>> Exclusions(this IMVExclude self)
        {
            var exclusions = new List<Tuple<double, double>>();
            for (int i = 0; i < self.ExclusionCount; i++)
            {
                exclusions.Add(Get(self, i));
            }

            return exclusions;
        }

        /// <summary>
        /// Verifies that the Exclusions can be saved and loaded correctly
        /// </summary>
        /// <param name="self">The IMVExclusion instance</param>
        public static void VerifyUserDescriptors(this IMVExclude self)
        {
            var exclusions = self.Exclusions();
            var temp = Path.Combine(Path.GetTempPath(), "temp.mpd");
            try
            {
                // dump exclusions to file and reset
                self.SaveExclusionsToFile(temp, 0);
                self.ClearAllExclusions();
                Debug.Assert(self.ExclusionCount == 0, "ClearAllExclusions failed");

                // reload exclusions from file
                self.LoadExclusionsFromFile(temp, 0);
            }
            finally
            {
                if (File.Exists(temp))
                {
                    File.Delete(temp);
                }
            }

            // verify that the exclusions were loaded correctly
            Debug.Assert(self.ExclusionCount == exclusions.Count);
            for (int i = 0; i < exclusions.Count; i++)
            {
                var tuple = Get(self, i);
                Debug.Assert(tuple.Equals(exclusions[i]));
            }
        }
    }
}

