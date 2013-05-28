namespace MVRuntimeLib
{
    using System;

    /// <summary>
    /// Indexed property accessor
    /// </summary>
    /// <typeparam name="TK">Data type of property's indexer variable</typeparam>
    /// <typeparam name="T">Data type of property's getter function</typeparam>
    public sealed class IndexedProperty<TK, T>
    {
        /// <summary>
        /// Getter function
        /// </summary>
        private readonly Func<TK, T> getter;

        /// <summary>
        /// Setter function
        /// </summary>
        private readonly Action<TK, T> setter;

        /// <summary>
        /// Constructor
        /// </summary>
        /// <param name="getter">Getter function to wrap with</param>
        /// <param name="setter">Setter function to wrap with</param>
        public IndexedProperty(Func<TK, T> getter = null, Action<TK, T> setter = null)
        {
            if (getter != null)
            {
                this.getter = getter;
            }

            if (setter != null)
            {
                this.setter = setter;
            }
        }

        /// <summary>
        /// Indexed access to getter and setter functions
        /// </summary>
        /// <param name="index">Index to access</param>
        /// <returns>Value as returned by wrapped getter function</returns>
        public T this[TK index]
        {
            get
            {
                if (this.getter == null)
                {
                    throw new NotImplementedException();
                }

                return this.getter(index);
            }
            set
            {
                if (this.setter == null)
                {
                    throw new NotImplementedException();
                }

                this.setter(index, value);
            }
        }
    }
}