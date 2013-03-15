//-----------------------------------------------------------------------
// <copyright file="IronBindings.cs" company="muvee Technologies Pte Ltd">
//   Copyright (c) muvee Technologies Pte Ltd. All rights reserved.
// </copyright>
// <author>Jerry Chong</author>
//-----------------------------------------------------------------------

using IronPython.Runtime;

[assembly: PythonModule("mvrt", typeof(MVRuntimeLib.IronBindings))]
namespace MVRuntimeLib
{
    using IronPython.Runtime;
    using System;
    using System.Reflection;
    using System.Runtime.CompilerServices;
    using System.Runtime.InteropServices;

    /// <summary>
    /// IronPython .NET bindings for the muvee COM interop
    /// </summary>
    public static class IronBindings
    {
        /// <summary>
        /// Called when "muvee" namespace is imported in Python, same as __init__.py
        /// </summary>
        /// <param name="context">Python context</param>
        /// <param name="dict">Python dictionary</param>
        [SpecialName]
        public static void PerformModuleReload(PythonContext context, PythonDictionary dict)
        {
            // do init here
            var asm = Assembly.GetAssembly(typeof(IMVCore));
            context.DomainManager.LoadAssembly(asm);
            Console.WriteLine("Imported MVRuntimeLib.");
        }

        /// <summary>
        /// Release the MVCore COM object
        /// </summary>
        public static void Release()
        {
            if (core == null)
            {
                return;
            }

            Marshal.FinalReleaseComObject(core);
            core = null;
            GC.Collect();
        }

        /// <summary>
        /// MVRuntime.MVCore instance
        /// </summary>
        private static IMVCore core;

        /// <summary>
        /// Getter function for MVRuntime.MVCore
        /// </summary>
        public static IMVCore Core
        {
            get
            {
                if (core == null)
                {
                    core = new MVCore() as IMVCore;
                    core.Init(0);
                }

                return core;
            }
        }
    }
}
