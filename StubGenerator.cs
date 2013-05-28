namespace MVRuntimeLib
{
    using System;
    using System.ComponentModel;
    using System.Linq;
    using System.Reflection;
    using System.Reflection.Emit;
    using System.Text;

    using Roslyn.Compilers;
    using Roslyn.Compilers.CSharp;

    /// <summary>
    /// Generates a wrapper stub around a given Class
    /// </summary>
    public sealed class StubGenerator
    {
        /// <summary>
        /// Template text used to generate the stub code body
        /// </summary>
        private const string Template = @"
namespace MVRuntimeLib
{
    public sealed class {dummy}Wrapper : {dummy}
    {
        private readonly {dummy} source;
        public {dummy}Wrapper({dummy} source) { this.source = source; }
        public new string ToString() { return source.ToString(); }
        public {dummy} __Source { get { return this.source; } }
        {methods}
    }
}
";

        /// <summary>
        /// Type of class to be wrapped
        /// </summary>
        public Type Target { get; private set; }

        /// <summary>
        /// Code body for the generated wrapper
        /// </summary>
        public string Code
        {
            get
            {
                return this.Generate();
            }
        }

        /// <summary>
        /// Constructor
        /// </summary>
        /// <param name="target">Type of class to be wrapped</param>
        public StubGenerator(Type target)
        {
            this.Target = target;
        }
        
        /// <summary>
        /// 
        /// </summary>
        /// <param name="method"></param>
        /// <returns></returns>
        private string GenerateMethod(MethodInfo method)
        {
            // whether there's a return type, or if 'void'
            var returnType = method.ReturnType == typeof(void) ? "void" : method.ReturnType.FullName;

            // whether we need a return statement
            var hasReturn = method.ReturnType != typeof(void) ? "return" : "";

            // list of accepted function parameters
            var args1 = string.Join(
                ", ",
                from parameter in method.GetParameters()
                select (Format(
                    "{out}{type} {name}",
                    new {
                            // whether passed by reference
                            @out = parameter.IsOut ? "out " : "",
                            @type =
                    parameter.ParameterType.IsByRef ? parameter.ParameterType.GetElementType() : parameter.ParameterType,
                            name = parameter.Name
                        })));

            // how to pass parameters to proxied object
            var args2 = "(" + string.Join(", ",
                            from parameter in method.GetParameters()
                            select (parameter.IsOut ? "out " : "") + parameter.Name) + ")";

            return this.Format(@"
public {returnType} {func}({args1}) {
    {hasReturn} source.{func2}{args2};
}
",
                new {
                        returnType,
                        hasReturn,
                        args1,
                        args2,
                        func = method.Name, // original method name
                        func2 = method.Name, // if property, remove the get_/set_ prefixes
                    });
        }

        /// <summary>
        /// Generates the function stub for an indexed class property
        /// </summary>
        /// <param name="property"></param>
        /// <returns></returns>
        private string GenerateIndexedProperty(PropertyInfo property)
        {
            var canReadWrite = (property.CanRead || property.CanWrite) ? "public" : "private";
            var setter = property.CanWrite ? @"(index, v) => { source.{set_name}(index, v); }" : "null";
            var code = @"
{canReadWrite} IndexedProperty<{indextype}, {datatype}> {name} {
    get {
        return new IndexedProperty<{indextype}, {datatype}>(
            index => source.{get_name}(index),
            " + setter + @");
    }
}
";

            // generate function body template
            return this.Format(
                code,
                new
                    {
                        indextype = property.GetIndexParameters()[0].ParameterType.FullName,
                        datatype = property.PropertyType.FullName,
                        name = property.Name,
                        get_name = property.CanRead ? property.GetGetMethod().Name : "",
                        set_name = property.CanWrite ? property.GetSetMethod().Name : "",
                        canReadWrite
                    });
        }

        /// <summary>
        /// Generates the function stub for a class property
        /// </summary>
        /// <param name="property"></param>
        /// <returns></returns>
        private string GenerateProperty(PropertyInfo property)
        {
            // indexed property
            if (property.GetIndexParameters().Length > 0)
            {
                return this.GenerateIndexedProperty(property);
            }

            var canReadWrite = (property.CanRead || property.CanWrite) ? "public" : "private";
            var canRead = (!property.CanRead && property.CanWrite) ? "private" : "";
            var canWrite = (!property.CanWrite && property.CanRead) ? "private" : "";
            var setter = property.CanWrite ? @"{canWrite} set { source.{name} = value; }" : "";
            var code = @"
{canReadWrite} {datatype} {name} {
    {canRead} get { return source.{name}; }
    " + setter + @"
}";

            // generate function body template
            return this.Format(
                code,
                new { datatype = property.PropertyType.FullName, name = property.Name, canRead, canWrite, canReadWrite });
        }

        /// <summary>
        /// Generates the wrapper stub for the given class T
        /// </summary>
        /// <returns>Code body for the stub</returns>
        internal string Generate()
        {
            var code = new StringBuilder();

            // accessors
            foreach (var property in this.Target.GetProperties())
            {
                code.Append(GenerateProperty(property));
            }

            // already generated property get/set methods in last step
            var generated =
                this.Target.GetProperties()
                    .Where(property => property.GetIndexParameters().Length == 0)
                    .Select(property => property.GetGetMethod())
                    .Union(this.Target.GetProperties().Select(property => property.GetSetMethod()))
                    .Where(method => method != null);

            // methods that are not property accessors
            foreach (var method in this.Target.GetMethods().Except(generated))
            {
                code.Append(this.GenerateMethod(method));
            }

            // join code into template
            return Format(Template, new { dummy = this.Target.Name, methods = code });
        }

        /// <summary>
        /// Invokes the Rosyln C# compiler to generate a dynamic assembly
        /// </summary>
        /// <exception cref="NotSupportedException">If the code fails to compile</exception>
        public ModuleBuilder Compile()
        {
            // generate a GUID as assembly name
            var name = new AssemblyName { Name = Guid.NewGuid().ToString("N") };
            var assemblyBuilder = AppDomain.CurrentDomain.DefineDynamicAssembly(name, AssemblyBuilderAccess.Run);

            // dynamic assembly
            var builder = assemblyBuilder.DefineDynamicModule(name.Name);

            // configure Roslyn output
            // { SyntaxTree.ParseText(this.Code) },
            var tree = SyntaxTree.ParseCompilationUnit(this.Code);
            var compiler = Compilation.Create(
                "Test",
                new CompilationOptions(OutputKind.DynamicallyLinkedLibrary),
                new[] { tree },
                new MetadataReference[]
                    {
                        // for 'using System'
                        // new MetadataFileReference(typeof(Guid).Assembly.Location),
                        new AssemblyFileReference(typeof(Guid).Assembly.Location), 

                        // reference to original proxied class
                        new AssemblyFileReference(this.Target.Assembly.Location),

                        // reference to IronBindings
                        new AssemblyFileReference(typeof(StubGenerator).Assembly.Location)
                    });

            // compile and store output in module
            var result = compiler.Emit(builder);
            if (!result.Success)
            {
                // print failed output
                throw new NotSupportedException(
                    string.Join(
                        Environment.NewLine,
                        from diagnostic in result.Diagnostics
                        select diagnostic.Location + ": " + diagnostic.Info.GetMessage()));
            }

            // return dynamic assembly
            return builder;
        }

        /// <summary>
        /// String format function supporting named parameters
        /// </summary>
        /// <param name="input">Template text to format</param>
        /// <param name="object">Object with which properties are used for formatting</param>
        /// <returns></returns>
        internal string Format(string input, object @object)
        {
            return TypeDescriptor.GetProperties(@object)
                                 .Cast<PropertyDescriptor>()
                                 .Aggregate(
                                     input,
                                     (current, prop) =>
                                     current.Replace(
                                         "{" + prop.Name + "}", (prop.GetValue(@object) ?? "(null)").ToString()));
        }
    }
}
